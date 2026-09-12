# CLAUDE.md — Aturan Utama Project

> Aplikasi: **AI Financial Assistant** (nama sementara)
> Pencatatan keuangan pribadi berbasis bahasa natural (terutama suara).

## 1. Ringkasan Produk
Pengguna mencatat pemasukan & pengeluaran dengan berbicara/mengetik bahasa
natural. AI mengekstrak: jenis transaksi, nominal, kategori, akun, dan tanggal,
lalu sistem mencatatnya otomatis.

Contoh: `"Beli kopi 35 ribu pakai BCA"` →
pengeluaran, Rp35.000, kategori Makanan & Minuman → Kopi, akun BCA, tanggal hari ini.

Detail visi lengkap: `docs/PRODUCT_VISION.md`.

## 2. Prinsip Kerja (WAJIB)
- **Bertahap.** Kerjakan HANYA task yang diminta saat ini. Tidak ada fitur di luar itu.
- **Tanpa over-engineering.** Solusi paling sederhana yang benar.
- **Tanpa file/dependency spekulatif.** Jangan buat file atau pasang dependency untuk kebutuhan hipotetis.
- **Jangan ganti konfigurasi yang sudah ada** tanpa alasan kuat.
- **Jelaskan dulu sebelum perubahan besar** (arsitektur, dependency baru, struktur folder).
- **Hemat token & context.** Baca hanya file yang relevan; jangan eksplorasi yang tidak perlu.

## 3. Sumber Konteks (baca ini, jangan tanya ulang)
1. `CLAUDE.md` — aturan & prinsip (file ini)
2. `docs/PROJECT_STATUS.md` — status terkini, yang sudah/belum dikerjakan
3. `docs/DECISIONS.md` — keputusan arsitektur & alasannya
4. `docs/PRODUCT_VISION.md` — tujuan produk & lingkup

## 4. Alur Setiap Task Berikutnya
1. Baca `CLAUDE.md`, `docs/PROJECT_STATUS.md`, `docs/DECISIONS.md`.
2. Periksa HANYA file yang relevan dengan task.
3. Kerjakan task.
4. Jalankan test yang relevan (jika ada).
5. Update `docs/PROJECT_STATUS.md`.
6. Jika ada keputusan arsitektur baru, update `docs/DECISIONS.md`.
7. Berikan ringkasan perubahan singkat.

Jangan mengulang pekerjaan yang sudah selesai (cek `PROJECT_STATUS.md` dulu).

## 5. Git
- Branch pengembangan: `claude/financial-assistant-setup-n1aqkd`.
- Commit dengan pesan jelas dan deskriptif.
- Jangan push ke branch lain tanpa izin eksplisit.
- Jangan buat Pull Request kecuali diminta.

## 6. Yang BELUM Diputuskan
Bahasa/framework, database, cara input suara (STT), dan penyedia model AI
**belum ditentukan**. Jangan asumsikan; tanyakan atau tunggu instruksi.
