"""Penyimpanan sementara (cache) di memori dengan masa berlaku.

Tujuan (NFR-04): menghemat kuota API gratis dan mempercepat halaman.
Catatan: di Vercel (serverless), memori ini hanya bertahan selama server
masih "hangat". Itu cukup membantu, tetapi bukan jaminan data selalu ada.
"""
import threading
import time


class TTLCache:
    """Menyimpan nilai bersama waktu kedaluwarsa (TTL = time to live, dalam detik)."""

    def __init__(self, ttl_detik=1800, jam=time.monotonic):
        self.ttl = ttl_detik
        self._jam = jam          # fungsi pengambil waktu (bisa diganti saat pengujian)
        self._data = {}          # kunci -> (nilai, waktu_kedaluwarsa)
        self._kunci = threading.Lock()

    def ambil(self, kunci):
        """Mengembalikan nilai bila masih berlaku, atau None bila kosong/kedaluwarsa."""
        with self._kunci:
            item = self._data.get(kunci)
            if item is None:
                return None
            nilai, kedaluwarsa = item
            if self._jam() >= kedaluwarsa:
                del self._data[kunci]
                return None
            return nilai

    def simpan(self, kunci, nilai):
        with self._kunci:
            self._data[kunci] = (nilai, self._jam() + self.ttl)

    def kosongkan(self):
        with self._kunci:
            self._data.clear()