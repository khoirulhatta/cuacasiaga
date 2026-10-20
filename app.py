from flask import Flask, jsonify
import requests

# static_folder="public": Flask membaca halaman dari folder public (saat lokal)
app = Flask(__name__, static_folder="public", static_url_path="")


@app.route("/")
def beranda():
    # Menampilkan public/index.html
    return app.send_static_file("index.html")


@app.route("/api/health")
def health():
    # Cek apakah server hidup
    return jsonify({"status": "ok"})


@app.route("/api/test-weather")
def test_weather():
    # Uji satu panggilan ke Open-Meteo: Palangka Raya
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": -2.21,
        "longitude": 113.92,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "timezone": "Asia/Jakarta",
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return jsonify(r.json())
    except requests.RequestException:
        return jsonify({"error": "Gagal mengambil data cuaca"}), 502


if __name__ == "__main__":
    app.run(debug=True)