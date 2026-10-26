import pytest

from services import risiko as r


def test_poin_suhu():
    assert r.poin_suhu(28) == 0
    assert r.poin_suhu(31) == 1
    assert r.poin_suhu(34) == 2
    assert r.poin_suhu(36) == 3


@pytest.mark.parametrize("fungsi,nilai,harapan", [
    (r.poin_hari_kering, 0, 0), (r.poin_hari_kering, 1, 0), (r.poin_hari_kering, 2, 1), (r.poin_hari_kering, 3, 1),
    (r.poin_hari_kering, 4, 2), (r.poin_hari_kering, 6, 2), (r.poin_hari_kering, 7, 3),
    (r.poin_hujan_7hari, 60, 0), (r.poin_hujan_7hari, 50, 1), (r.poin_hujan_7hari, 20, 1),
    (r.poin_hujan_7hari, 19.9, 2), (r.poin_hujan_7hari, 5, 2), (r.poin_hujan_7hari, 4.9, 3),
    (r.poin_suhu, 29.9, 0), (r.poin_suhu, 30, 1), (r.poin_suhu, 32.9, 1), (r.poin_suhu, 33, 2),
    (r.poin_suhu, 34.9, 2), (r.poin_suhu, 35, 3),
    (r.poin_kelembapan, 85, 0), (r.poin_kelembapan, 80, 1), (r.poin_kelembapan, 70, 1),
    (r.poin_kelembapan, 69, 2), (r.poin_kelembapan, 55, 2), (r.poin_kelembapan, 54, 3),
    (r.poin_angin, 9.9, 0), (r.poin_angin, 10, 1), (r.poin_angin, 19.9, 1), (r.poin_angin, 20, 2),
    (r.poin_angin, 29.9, 2), (r.poin_angin, 30, 3),
    (r.poin_hotspot, 0, 0), (r.poin_hotspot, 2, 1), (r.poin_hotspot, 3, 2), (r.poin_hotspot, 9, 2), (r.poin_hotspot, 10, 3),
])
def test_batas_poin(fungsi, nilai, harapan):
    assert fungsi(nilai) == harapan


@pytest.mark.parametrize("persen,kategori", [
    (0, "Rendah"), (25, "Rendah"), (26, "Sedang"), (50, "Sedang"),
    (51, "Tinggi"), (75, "Tinggi"), (76, "Sangat tinggi"), (100, "Sangat tinggi"),
])
def test_kategori(persen, kategori):
    assert r.kategori_dari_persen(persen) == kategori


def test_hitung_skor_lima_faktor():
    poin = {"a": 2, "b": 3, "c": 2, "d": 2, "e": 1}      # contoh di halaman: 10 dari 15
    assert r.hitung_skor(poin) == (10, 15, 67, "Tinggi")


def test_hitung_skor_mengabaikan_faktor_kosong():
    poin = {"a": 3, "b": 3, "c": 3, "d": None, "e": None}
    skor, maks, persen, kategori = r.hitung_skor(poin)
    assert (skor, maks, persen, kategori) == (9, 9, 100, "Sangat tinggi")


def test_data_kurang_dari_tiga_faktor():
    with pytest.raises(r.DataTidakCukup):
        r.hitung_skor({"a": 3, "b": 3, "c": None, "d": None, "e": None})


def test_masukan_dari_data_mentah(data_contoh):
    m = r.masukan_dari_data_mentah(data_contoh)
    assert m["hari_kering"] == 5          # 24, 23, 22, 21, 20 Okt kering; 19 Okt hujan 6 mm
    assert m["hujan_7hari"] == 20.9
    assert m["suhu_maks"] == 34
    assert m["kelembapan"] == 62
    assert m["angin"] == 12.4


def test_hari_kering_maksimum_tujuh(data_contoh):
    data_contoh["daily"]["precipitation_sum"][:7] = [0.0] * 7
    assert r.masukan_dari_data_mentah(data_contoh)["hari_kering"] == 7


def test_hitung_kewaspadaan_lengkap(data_contoh):
    hasil = r.hitung_kewaspadaan(data_contoh)
    # poin: hari kering 5 -> 2, hujan 20,9 -> 1, suhu 34 -> 2, kelembapan 62 -> 2, angin 12,4 -> 1
    assert (hasil["skor"], hasil["skor_maks"], hasil["persen"]) == (8, 15, 53)
    assert hasil["kategori"] == "Tinggi"
    assert len(hasil["faktor"]) == 5
    assert "Skor dihitung tanpa data hotspot." in hasil["catatan"]
    assert "bukan peringatan resmi" in hasil["disclaimer"]


def test_hotspot_menambah_faktor(data_contoh):
    hasil = r.hitung_kewaspadaan(data_contoh, jumlah_hotspot=12)
    assert hasil["skor_maks"] == 18 and hasil["skor"] == 11 and hasil["persen"] == 61
    assert hasil["faktor"][-1]["kode"] == "hotspot"
    assert hasil["catatan"] == []


def test_data_cuaca_tidak_cukup(data_contoh):
    data_contoh["daily"]["time"] = ["2020-01-01"] * 14      # tanggal hari ini tidak ditemukan
    with pytest.raises(r.DataTidakCukup):
        r.hitung_kewaspadaan(data_contoh)