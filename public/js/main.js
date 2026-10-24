// main.js: tahap P1 (tampilan saja).
// Bagian ini hanya mengganti nama lokasi di halaman saat pilihan berubah.
// Angka cuaca masih data contoh. Di tahap P2, di sinilah kita memanggil /api/weather.

const pilihLokasi = document.getElementById('pilih-lokasi');
const namaLokasi = document.querySelectorAll('[data-lokasi]');

pilihLokasi.addEventListener('change', function () {
    // Ganti teks setiap elemen yang punya atribut data-lokasi
    namaLokasi.forEach(function (el) {
        el.textContent = pilihLokasi.value;
    });
});