"""Indikator kewaspadaan karhutla berbasis aturan skor.

Ambang batas mengikuti tabel di PRD Bab 11 dan merupakan DRAF ASUMSI, terinspirasi
konsep Fire Weather Index (FWI). Ini bukan standar resmi dan hasilnya indikatif.

Cara kerja: setiap faktor diberi poin 0-3, poin dijumlahkan, lalu dijadikan persen
dari skor maksimum faktor yang tersedia. Persen itu menentukan kategori.
"""

DISCLAIMER = "Hasil ini indikatif dan bukan peringatan resmi."
AMBANG_HARI_KERING_MM = 1.0   # sebuah hari dianggap kering bila hujannya di bawah 1 mm
MIN_FAKTOR = 3                # skor hanya dihitung bila minimal 3 faktor tersedia


class DataTidakCukup(Exception):
    """Data cuaca terlalu sedikit untuk menghitung skor."""


# ---------- Poin per faktor (0 sampai 3) ----------
def poin_hari_kering(hari):
    if hari >= 7:
        return 3
    if hari >= 4:
        return 2
    if hari >= 2:
        return 1
    return 0


def poin_hujan_7hari(mm):
    if mm < 5:
        return 3
    if mm < 20:
        return 2
    if mm <= 50:
        return 1
    return 0


def poin_suhu(suhu_maks):
    """Poin 0-3 dari suhu maksimum harian."""
    if suhu_maks < 30:
        return 0
    if suhu_maks < 33:
        return 1
    if suhu_maks < 35:
        return 2
    return 3


def poin_kelembapan(persen):
    if persen < 55:
        return 3
    if persen < 70:
        return 2
    if persen <= 80:
        return 1
    return 0


def poin_angin(km_per_jam):
    if km_per_jam >= 30:
        return 3
    if km_per_jam >= 20:
        return 2
    if km_per_jam >= 10:
        return 1
    return 0


def poin_hotspot(jumlah):
    if jumlah >= 10:
        return 3
    if jumlah >= 3:
        return 2
    if jumlah >= 1:
        return 1
    return 0


# ---------- Skor dan kategori ----------
def kategori_dari_persen(persen):
    if persen <= 25:
        return "Rendah"
    if persen <= 50:
        return "Sedang"
    if persen <= 75:
        return "Tinggi"
    return "Sangat tinggi"


def hitung_skor(poin):
    """poin: dict {kode_faktor: poin atau None}. Faktor yang None diabaikan.

    Mengembalikan (skor, skor_maks, persen, kategori).
    """
    tersedia = [p for p in poin.values() if p is not None]
    if len(tersedia) < MIN_FAKTOR:
        raise DataTidakCukup("Faktor yang tersedia kurang dari %d." % MIN_FAKTOR)
    skor = sum(tersedia)
    skor_maks = 3 * len(tersedia)
    persen = int(skor / skor_maks * 100 + 0.5)   # dibulatkan ke bilangan bulat
    return skor, skor_maks, persen, kategori_dari_persen(persen)


# ---------- Mengambil masukan dari data Open-Meteo ----------
def _ambil(daftar, i):
    return daftar[i] if daftar is not None and 0 <= i < len(daftar) else None


def masukan_dari_data_mentah(mentah):
    """Menghitung nilai tiap faktor dari data Open-Meteo (past_days=7).

    - hari_kering: jumlah hari kering berturut-turut, dihitung mundur dari kemarin (maks 7)
    - hujan_7hari: total hujan selama 7 hari sebelum hari ini
    - suhu_maks, angin: nilai maksimum hari ini
    - kelembapan: rata-rata kelembapan per jam hari ini
    """
    kosong = {"hari_kering": None, "hujan_7hari": None, "suhu_maks": None, "kelembapan": None, "angin": None}
    d, h = mentah["daily"], mentah["hourly"]
    hari_ini = mentah["current"]["time"][:10]
    tanggal = d.get("time", [])
    if hari_ini not in tanggal:
        return kosong
    i = tanggal.index(hari_ini)
    hujan = d.get("precipitation_sum") or []
    lalu = [_ambil(hujan, j) for j in range(max(0, i - 7), i)]    # 7 hari sebelum hari ini

    hasil = dict(kosong)
    if sum(1 for v in lalu if v is not None) >= 3:
        kering = 0
        for v in reversed(lalu):                                   # mulai dari kemarin
            if v is not None and v < AMBANG_HARI_KERING_MM:
                kering += 1
            else:
                break
        hasil["hari_kering"] = kering
        hasil["hujan_7hari"] = round(sum(v for v in lalu if v is not None), 1)
    hasil["suhu_maks"] = _ambil(d.get("temperature_2m_max"), i)
    hasil["angin"] = _ambil(d.get("wind_speed_10m_max"), i)
    nilai_rh = [v for t, v in zip(h.get("time", []), h.get("relative_humidity_2m") or [])
                if t.startswith(hari_ini) and v is not None]
    if nilai_rh:
        hasil["kelembapan"] = round(sum(nilai_rh) / len(nilai_rh))
    return hasil


# (kode, nama tampil, satuan, fungsi poin)
FAKTOR = [
    ("hari_kering", "Hari kering berturut-turut", "hari", poin_hari_kering),
    ("hujan_7hari", "Total hujan 7 hari", "mm", poin_hujan_7hari),
    ("suhu_maks", "Suhu maksimum", "\u00b0C", poin_suhu),
    ("kelembapan", "Kelembapan", "%", poin_kelembapan),
    ("angin", "Kecepatan angin", "km/jam", poin_angin),
]


def hitung_kewaspadaan(mentah, jumlah_hotspot=None):
    """Hasil lengkap untuk /api/fire-risk. jumlah_hotspot=None berarti data hotspot tidak dipakai."""
    masukan = masukan_dari_data_mentah(mentah)
    poin, rincian = {}, []
    for kode, nama, satuan, fungsi in FAKTOR:
        nilai = masukan[kode]
        poin[kode] = fungsi(nilai) if nilai is not None else None
        if nilai is not None:
            rincian.append({"kode": kode, "nama": nama, "nilai": nilai, "satuan": satuan, "poin": poin[kode], "poin_maks": 3})
    catatan = []
    if jumlah_hotspot is None:
        catatan.append("Skor dihitung tanpa data hotspot.")
    else:
        poin["hotspot"] = poin_hotspot(jumlah_hotspot)
        rincian.append({"kode": "hotspot", "nama": "Hotspot radius 50 km", "nilai": jumlah_hotspot,
                        "satuan": "titik", "poin": poin["hotspot"], "poin_maks": 3})
    if any(masukan[k] is None for k, *_ in FAKTOR):
        catatan.append("Sebagian faktor cuaca tidak tersedia dan tidak ikut dihitung.")
    skor, skor_maks, persen, kategori = hitung_skor(poin)
    return {"kategori": kategori, "skor": skor, "skor_maks": skor_maks, "persen": persen,
            "faktor": rincian, "catatan": catatan, "disclaimer": DISCLAIMER}