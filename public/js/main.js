// main.js - P2 langkah 2: mengambil data dari backend Flask lalu menampilkannya.
// Alur: halaman terbuka -> ambil daftar lokasi -> ambil cuaca + prakiraan -> tampilkan.

// Dipakai bila daftar lokasi dari server gagal dimuat
const LOKASI_BAWAAN = { nama: 'Palangka Raya', provinsi: 'Kalimantan Tengah', lat: -2.21, lon: 113.92 };
const NAMA_HARI = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'];

const $ = (id) => document.getElementById(id);   // jalan pintas: ambil elemen berdasarkan id
let daftarLokasi = [];
let permintaanTerakhir = 0;   // untuk mengabaikan jawaban lama bila pengguna cepat berganti lokasi

// ---------- Alat bantu ----------
async function ambilJSON(url) {
    const respons = await fetch(url);
    let isi = {};
    try { isi = await respons.json(); } catch (e) { /* respons bukan JSON */ }
    if (!respons.ok) throw new Error(isi.error || 'Terjadi kesalahan saat memuat data.');
    return isi;
}

function angka(n, satuan = '') {
    return (n === null || n === undefined) ? '-' : Math.round(n) + satuan;
}

function buat(tag, kelas, teks) {
    const el = document.createElement(tag);
    if (kelas) el.className = kelas;
    if (teks !== undefined) el.textContent = teks;   // textContent aman: teks tidak dibaca sebagai HTML
    return el;
}

function namaHari(tanggal, urutan) {
    if (urutan === 0) return 'Hari ini';
    const [y, m, d] = tanggal.split('-').map(Number);
    return NAMA_HARI[new Date(y, m - 1, d).getDay()];
}

// ---------- Menampilkan data ke halaman ----------
function tampilkanCuaca(d) {
    $('suhu').textContent = angka(d.suhu);
    $('kondisi').textContent = d.kondisi;
    $('kelembapan').textContent = angka(d.kelembapan, '%');
    $('angin').textContent = angka(d.angin, ' km/jam');
    $('curah').textContent = (d.curah_hujan === null || d.curah_hujan === undefined) ? '-' : Number(d.curah_hujan.toFixed(1)) + ' mm';
    $('peluang').textContent = angka(d.peluang_hujan, '%');
    const jamCuaca = d.waktu.slice(11, 16);
    const jamAmbil = new Date(d.diperbarui).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });
    $('meta-cuaca').textContent = 'Cuaca pukul ' + jamCuaca + ' ' + (d.zona_waktu || '') + '. Data diambil pukul ' + jamAmbil +
        (d.dari_cache ? ' (dari cache)' : '') + '. Sumber: Open-Meteo.com.';
}

function tampilkanPerJam(daftar) {
    const ol = $('daftar-jam');
    ol.replaceChildren();   // hapus isi lama (data contoh atau lokasi sebelumnya)
    daftar.forEach(function (j, i) {
        const li = buat('li');
        const batang = buat('span', 'hujan');
        batang.style.setProperty('--p', j.peluang_hujan === null ? 0 : j.peluang_hujan);
        li.append(buat('span', 'j-waktu', i === 0 ? 'Sekarang' : j.waktu.slice(11, 16)),
            buat('span', 'j-suhu', angka(j.suhu, '\u00b0')),
            batang,
            buat('span', 'j-hujan', angka(j.peluang_hujan, '%')));
        ol.append(li);
    });
}

function tampilkanPerHari(daftar) {
    const ul = $('daftar-hari');
    ul.replaceChildren();
    const batas = (n) => Math.min(36, Math.max(22, n));   // batang suhu memakai skala 22-36 derajat
    daftar.forEach(function (h, i) {
        const li = buat('li');
        const rentang = buat('span', 'rentang');
        const isi = buat('span');
        isi.style.setProperty('--min', batas(h.suhu_min));
        isi.style.setProperty('--maks', batas(h.suhu_maks));
        rentang.append(isi);
        li.append(buat('span', 'h-nama', namaHari(h.tanggal, i)),
            buat('span', 'h-kondisi', h.kondisi),
            rentang,
            buat('span', 'h-suhu', angka(h.suhu_min, '\u00b0') + ' / ' + angka(h.suhu_maks, '\u00b0')),
            buat('span', 'h-hujan', 'Hujan ' + angka(h.peluang_hujan_maks, '%')));
        ul.append(li);
    });
}

function tampilkanKesalahan(pesan) {
    $('teks-kesalahan').textContent = pesan;
    $('pesan-kesalahan').hidden = false;
    $('status').textContent = '';
}

// ---------- Memuat data satu lokasi ----------
async function muatData(lokasi) {
    const nomor = ++permintaanTerakhir;
    const bagian = document.querySelectorAll('.cuaca, .prakiraan');
    bagian.forEach(function (b) { b.classList.add('memuat'); });
    $('status').textContent = 'Memuat data cuaca...';
    $('pesan-kesalahan').hidden = true;
    document.querySelectorAll('[data-lokasi]').forEach(function (e) { e.textContent = lokasi.label; });

    const kueri = 'lat=' + lokasi.lat + '&lon=' + lokasi.lon;
    try {
        const cuaca = await ambilJSON('/api/weather?' + kueri);
        const prakiraan = await ambilJSON('/api/forecast?' + kueri);   // berurutan agar memakai cache
        if (nomor !== permintaanTerakhir) return;                      // ada permintaan yang lebih baru
        tampilkanCuaca(cuaca);
        tampilkanPerJam(prakiraan.per_jam);
        tampilkanPerHari(prakiraan.per_hari);
        $('catatan-judul').textContent = 'Data cuaca nyata.';
        $('catatan-isi').textContent = 'Cuaca, prakiraan per jam, dan prakiraan 7 hari berasal dari Open-Meteo. Bagian kewaspadaan karhutla masih contoh dan dihitung di tahap berikutnya.';
        $('status').textContent = '';
    } catch (e) {
        if (nomor !== permintaanTerakhir) return;
        tampilkanKesalahan(e instanceof TypeError
            ? 'Tidak dapat terhubung ke server. Periksa koneksi internet lalu coba lagi.'
            : e.message);
    } finally {
        if (nomor === permintaanTerakhir) bagian.forEach(function (b) { b.classList.remove('memuat'); });
    }
}

// ---------- Memulai halaman ----------
async function mulai() {
    const pilih = $('pilih-lokasi');
    try {
        daftarLokasi = await ambilJSON('/api/lokasi');
    } catch (e) {
        daftarLokasi = [];
    }
    if (daftarLokasi.length === 0) daftarLokasi = [LOKASI_BAWAAN];

    daftarLokasi.forEach(function (k) { k.label = k.nama + ', ' + k.provinsi; });
    pilih.replaceChildren();
    daftarLokasi.forEach(function (k, i) {
        const opsi = buat('option', '', k.label);
        opsi.value = i;
        pilih.append(opsi);
    });

    const lokasiTerpilih = function () { return daftarLokasi[Number(pilih.value)]; };
    pilih.addEventListener('change', function () { muatData(lokasiTerpilih()); });
    $('coba-lagi').addEventListener('click', function () { muatData(lokasiTerpilih()); });

    muatData(lokasiTerpilih());
}

mulai();