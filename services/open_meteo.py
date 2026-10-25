"""Mengambil dan merapikan data cuaca dari Open-Meteo (https://open-meteo.com).

Wajib menampilkan atribusi "Weather data by Open-Meteo.com" pada situs.
"""
import math

import requests

URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_DETIK = 10

# Batas kasar wilayah Indonesia (validasi masukan, NFR-05)
LAT_MIN, LAT_MAKS = -11.5, 6.5
LON_MIN, LON_MAKS = 94.0, 141.5

# Kode cuaca WMO yang dipakai Open-Meteo -> teks bahasa Indonesia
KONDISI = {
    0: "Cerah", 1: "Cerah berawan", 2: "Berawan sebagian", 3: "Berawan",
    45: "Berkabut", 48: "Berkabut",
    51: "Gerimis ringan", 53: "Gerimis", 55: "Gerimis lebat",
    56: "Gerimis beku", 57: "Gerimis beku",
    61: "Hujan ringan", 63: "Hujan sedang", 65: "Hujan lebat",
    66: "Hujan beku", 67: "Hujan beku",
    71: "Salju ringan", 73: "Salju", 75: "Salju lebat", 77: "Butiran salju",
    80: "Hujan lokal ringan", 81: "Hujan lokal sedang", 82: "Hujan lokal lebat",
    85: "Hujan salju ringan", 86: "Hujan salju lebat",
    95: "Badai petir", 96: "Badai petir dan hujan es", 99: "Badai petir dan hujan es lebat",
}


class KoordinatTidakValid(ValueError):
    """Koordinat bukan angka atau di luar wilayah Indonesia."""


class GagalAmbilData(Exception):
    """Open-Meteo tidak dapat dihubungi atau responsnya tidak sesuai."""


def kondisi_dari_kode(kode):
    return KONDISI.get(kode, "Tidak diketahui")


def validasi_koordinat(lat, lon):
    """Memeriksa lat/lon, lalu membulatkannya ke 2 desimal (juga dipakai sebagai kunci cache)."""
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        raise KoordinatTidakValid("Koordinat harus berupa angka.")
    if not (math.isfinite(lat) and math.isfinite(lon)):
        raise KoordinatTidakValid("Koordinat harus berupa angka.")
    if not (LAT_MIN <= lat <= LAT_MAKS and LON_MIN <= lon <= LON_MAKS):
        raise KoordinatTidakValid("Koordinat di luar wilayah Indonesia.")
    return round(lat, 2), round(lon, 2)


def ambil_cuaca_mentah(lat, lon):
    """Satu kali panggilan ke Open-Meteo: cuaca saat ini, per jam, dan harian."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
        "hourly": "temperature_2m,precipitation_probability,precipitation",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum",
        "timezone": "auto",
        "forecast_days": 7,
    }
    try:
        r = requests.get(URL, params=params, timeout=TIMEOUT_DETIK)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError) as e:
        raise GagalAmbilData(str(e)) from e
    if not all(k in data for k in ("current", "hourly", "daily")):
        raise GagalAmbilData("Format respons Open-Meteo tidak sesuai.")
    return data


def _ambil(daftar, i):
    """Mengambil elemen ke-i dari daftar, atau None bila tidak ada."""
    return daftar[i] if daftar is not None and 0 <= i < len(daftar) else None


def indeks_jam_sekarang(mentah):
    """Posisi jam saat ini di dalam daftar per jam (contoh: '2026-10-25T14' cocok dengan '2026-10-25T14:00')."""
    jam_ini = mentah["current"]["time"][:13]
    for i, t in enumerate(mentah["hourly"]["time"]):
        if t[:13] == jam_ini:
            return i
    return 0


def ringkas_saat_ini(mentah):
    """Cuaca saat ini dalam bentuk ringkas untuk /api/weather."""
    c, h = mentah["current"], mentah["hourly"]
    i = indeks_jam_sekarang(mentah)
    return {
        "waktu": c["time"],
        "zona_waktu": mentah.get("timezone_abbreviation"),
        "suhu": c.get("temperature_2m"),
        "kelembapan": c.get("relative_humidity_2m"),
        "angin": c.get("wind_speed_10m"),
        "curah_hujan": c.get("precipitation"),
        "kode_cuaca": c.get("weather_code"),
        "kondisi": kondisi_dari_kode(c.get("weather_code")),
        "peluang_hujan": _ambil(h.get("precipitation_probability"), i),
    }


def ringkas_prakiraan(mentah, jumlah_jam=48):
    """Prakiraan per jam (mulai jam ini) dan 7 hari untuk /api/forecast."""
    h, d = mentah["hourly"], mentah["daily"]
    mulai = indeks_jam_sekarang(mentah)
    per_jam = []
    for i in range(mulai, min(mulai + jumlah_jam, len(h["time"]))):
        per_jam.append({
            "waktu": h["time"][i],
            "suhu": _ambil(h.get("temperature_2m"), i),
            "peluang_hujan": _ambil(h.get("precipitation_probability"), i),
            "curah_hujan": _ambil(h.get("precipitation"), i),
        })
    per_hari = []
    for i, tanggal in enumerate(d["time"]):
        kode = _ambil(d.get("weather_code"), i)
        per_hari.append({
            "tanggal": tanggal,
            "kode_cuaca": kode,
            "kondisi": kondisi_dari_kode(kode),
            "suhu_min": _ambil(d.get("temperature_2m_min"), i),
            "suhu_maks": _ambil(d.get("temperature_2m_max"), i),
            "peluang_hujan_maks": _ambil(d.get("precipitation_probability_max"), i),
            "curah_hujan_total": _ambil(d.get("precipitation_sum"), i),
        })
    return {"zona_waktu": mentah.get("timezone_abbreviation"), "per_jam": per_jam, "per_hari": per_hari}