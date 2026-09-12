# PRODUCT VISION — AI Financial Assistant

## Tujuan Utama
Pengguna cukup **berbicara**, AI memahami, sistem **mencatat transaksi otomatis**.
Mengurangi friksi pencatatan keuangan pribadi seminimal mungkin.

## Masalah yang Diselesaikan
Pencatatan keuangan manual itu merepotkan (buka app, pilih kategori, ketik
nominal), sehingga sering tidak konsisten. Dengan input bahasa natural/suara,
mencatat jadi secepat mengucapkan satu kalimat.

## Cara Kerja (konsep)
1. Pengguna mengucapkan/mengetik kalimat natural.
2. AI mengekstrak entitas transaksi:
   - **Jenis**: pemasukan / pengeluaran
   - **Nominal**: mis. Rp35.000
   - **Kategori & subkategori**: mis. Makanan & Minuman → Kopi
   - **Akun/sumber dana**: mis. BCA, tunai, e-wallet
   - **Tanggal**: default hari ini, atau sesuai ucapan ("kemarin", "3 hari lalu")
3. Sistem menyimpan transaksi terstruktur.

### Contoh
| Ucapan | Jenis | Nominal | Kategori | Akun | Tanggal |
|---|---|---|---|---|---|
| "Beli kopi 35 ribu pakai BCA" | Pengeluaran | 35.000 | Makanan & Minuman → Kopi | BCA | Hari ini |

## Prinsip Produk
- **Suara/bahasa natural sebagai input utama.**
- **Cepat & rendah friksi** — satu kalimat = satu transaksi tercatat.
- **Pribadi** — data keuangan milik satu pengguna.
- **Bertahap** — dibangun fitur demi fitur, bukan sekaligus.

## Di Luar Lingkup (untuk sekarang)
Investasi, multi-user/kolaborasi, integrasi bank otomatis, dan pelaporan pajak
**belum** menjadi fokus. Bisa dipertimbangkan setelah inti pencatatan stabil.

## Target Awal (indikatif, belum final)
Alur inti: **input natural → ekstraksi AI → simpan transaksi → lihat riwayat.**
