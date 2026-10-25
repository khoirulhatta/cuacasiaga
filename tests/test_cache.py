from services.cache import TTLCache


class JamPalsu:
    """Jam buatan agar tes bisa 'memajukan waktu' tanpa menunggu."""
    def __init__(self):
        self.sekarang = 0.0
    def __call__(self):
        return self.sekarang


def test_simpan_dan_ambil():
    cache = TTLCache(ttl_detik=60, jam=JamPalsu())
    assert cache.ambil("a") is None
    cache.simpan("a", {"nilai": 1})
    assert cache.ambil("a") == {"nilai": 1}


def test_kedaluwarsa_setelah_ttl():
    jam = JamPalsu()
    cache = TTLCache(ttl_detik=60, jam=jam)
    cache.simpan("a", "x")
    jam.sekarang = 59
    assert cache.ambil("a") == "x"
    jam.sekarang = 61
    assert cache.ambil("a") is None


def test_kosongkan():
    cache = TTLCache(ttl_detik=60, jam=JamPalsu())
    cache.simpan("a", "x")
    cache.kosongkan()
    assert cache.ambil("a") is None