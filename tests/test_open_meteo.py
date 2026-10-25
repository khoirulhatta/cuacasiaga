import pytest

from services import open_meteo as om


def test_koordinat_valid_dibulatkan():
    assert om.validasi_koordinat("-2.2149", "113.9201") == (-2.21, 113.92)


@pytest.mark.parametrize("lat,lon", [
    (None, "113.9"), ("abc", "113.9"), ("-2.2", ""), ("nan", "113.9"),
    ("45", "113.9"),      # lintang di luar Indonesia
    ("-2.2", "10"),       # bujur di luar Indonesia
])
def test_koordinat_tidak_valid(lat, lon):
    with pytest.raises(om.KoordinatTidakValid):
        om.validasi_koordinat(lat, lon)


def test_kondisi_dari_kode():
    assert om.kondisi_dari_kode(0) == "Cerah"
    assert om.kondisi_dari_kode(65) == "Hujan lebat"
    assert om.kondisi_dari_kode(999) == "Tidak diketahui"
    assert om.kondisi_dari_kode(None) == "Tidak diketahui"


def test_ringkas_saat_ini(data_contoh):
    hasil = om.ringkas_saat_ini(data_contoh)
    assert hasil["suhu"] == 33.1
    assert hasil["kelembapan"] == 62
    assert hasil["angin"] == 12.4
    assert hasil["kondisi"] == "Cerah berawan"
    assert hasil["zona_waktu"] == "WIB"
    # peluang hujan diambil dari jam 14:00 (indeks 14)
    assert hasil["peluang_hujan"] == data_contoh["hourly"]["precipitation_probability"][14]


def test_ringkas_prakiraan(data_contoh):
    hasil = om.ringkas_prakiraan(data_contoh)
    assert len(hasil["per_jam"]) == 48
    assert hasil["per_jam"][0]["waktu"] == "2026-10-25T14:00"
    assert len(hasil["per_hari"]) == 7
    assert hasil["per_hari"][2]["kondisi"] == "Hujan ringan"
    assert hasil["per_hari"][0]["suhu_maks"] == 34


def test_prakiraan_tidak_melebihi_data(data_contoh):
    hasil = om.ringkas_prakiraan(data_contoh, jumlah_jam=1000)
    assert len(hasil["per_jam"]) == 7 * 24 - 14