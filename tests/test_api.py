import pytest

import app as modul_app
from services import open_meteo as om


@pytest.fixture
def klien():
    modul_app.cache_cuaca.kosongkan()   # setiap tes mulai dengan cache kosong
    modul_app.app.config["TESTING"] = True
    return modul_app.app.test_client()


@pytest.fixture
def api_palsu(monkeypatch, data_contoh):
    """Mengganti pemanggilan Open-Meteo dengan data tiruan dan menghitung berapa kali dipanggil."""
    panggilan = []
    def palsu(lat, lon):
        panggilan.append((lat, lon))
        return data_contoh
    monkeypatch.setattr(om, "ambil_cuaca_mentah", palsu)
    return panggilan


def test_health(klien):
    assert klien.get("/api/health").get_json() == {"status": "ok"}


def test_lokasi(klien):
    data = klien.get("/api/lokasi").get_json()
    assert len(data) >= 5
    for k in data:
        assert {"nama", "provinsi", "lat", "lon"} <= set(k)


def test_weather_berhasil(klien, api_palsu):
    r = klien.get("/api/weather?lat=-2.21&lon=113.92")
    assert r.status_code == 200
    j = r.get_json()
    assert j["suhu"] == 33.1 and j["kondisi"] == "Cerah berawan"
    assert j["sumber"] == "Open-Meteo.com"
    assert j["dari_cache"] is False
    assert "diperbarui" in j


def test_panggilan_kedua_memakai_cache(klien, api_palsu):
    klien.get("/api/weather?lat=-2.21&lon=113.92")
    j = klien.get("/api/forecast?lat=-2.21&lon=113.92").get_json()
    assert j["dari_cache"] is True
    assert len(api_palsu) == 1      # Open-Meteo hanya dipanggil sekali untuk lokasi yang sama


def test_forecast_berhasil(klien, api_palsu):
    j = klien.get("/api/forecast?lat=-0.03&lon=109.34").get_json()
    assert len(j["per_jam"]) == 48 and len(j["per_hari"]) == 7


@pytest.mark.parametrize("url", ["/api/weather", "/api/weather?lat=abc&lon=1", "/api/forecast?lat=50&lon=113"])
def test_masukan_tidak_valid(klien, api_palsu, url):
    r = klien.get(url)
    assert r.status_code == 400 and "error" in r.get_json()
    assert api_palsu == []          # API tidak dipanggil bila masukan salah


def test_open_meteo_gagal(klien, monkeypatch):
    def gagal(lat, lon):
        raise om.GagalAmbilData("simulasi gangguan")
    monkeypatch.setattr(om, "ambil_cuaca_mentah", gagal)
    r = klien.get("/api/weather?lat=-2.21&lon=113.92")
    assert r.status_code == 502 and "error" in r.get_json()