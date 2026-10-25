"""WeatherGuard - backend Flask.

Alur: browser -> Flask (/api/...) -> cache -> Open-Meteo.
"""
import json
import os
from datetime import datetime, timezone

from flask import Flask, jsonify, request

from services import open_meteo as om
from services.cache import TTLCache

# static_folder="public": saat dijalankan lokal, Flask menampilkan isi folder public
app = Flask(__name__, static_folder="public", static_url_path="")

# Hasil Open-Meteo disimpan 30 menit per lokasi (NFR-04)
cache_cuaca = TTLCache(ttl_detik=30 * 60)

FOLDER_PROYEK = os.path.dirname(os.path.abspath(__file__))


def muat_lokasi():
    """Membaca daftar kota dari data/lokasi.json."""
    with open(os.path.join(FOLDER_PROYEK, "data", "lokasi.json"), encoding="utf-8") as f:
        return json.load(f)


def ambil_data_cuaca(lat, lon):
    """Mengambil data dari cache; bila tidak ada, memanggil Open-Meteo lalu menyimpannya.

    Mengembalikan (paket, dari_cache).
    """
    kunci = (lat, lon)
    paket = cache_cuaca.ambil(kunci)
    if paket is not None:
        return paket, True
    mentah = om.ambil_cuaca_mentah(lat, lon)
    paket = {
        "data": mentah,
        "diperbarui": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    cache_cuaca.simpan(kunci, paket)
    return paket, False


def jawab_cuaca(ringkas):
    """Pola yang sama untuk /api/weather dan /api/forecast."""
    try:
        lat, lon = om.validasi_koordinat(request.args.get("lat"), request.args.get("lon"))
    except om.KoordinatTidakValid as e:
        return jsonify({"error": str(e)}), 400
    try:
        paket, dari_cache = ambil_data_cuaca(lat, lon)
    except om.GagalAmbilData:
        return jsonify({"error": "Data cuaca belum bisa dimuat. Coba lagi beberapa saat."}), 502
    hasil = ringkas(paket["data"])
    hasil.update({
        "lokasi": {"lat": lat, "lon": lon},
        "diperbarui": paket["diperbarui"],
        "dari_cache": dari_cache,
        "sumber": "Open-Meteo.com",
    })
    return jsonify(hasil)


@app.get("/")
def beranda():
    return app.send_static_file("index.html")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/lokasi")
def lokasi():
    return jsonify(muat_lokasi())


@app.get("/api/weather")
def weather():
    return jawab_cuaca(om.ringkas_saat_ini)


@app.get("/api/forecast")
def forecast():
    return jawab_cuaca(om.ringkas_prakiraan)


if __name__ == "__main__":
    app.run(debug=True)