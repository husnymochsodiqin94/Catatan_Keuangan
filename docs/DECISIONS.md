# DECISIONS — Catatan Keputusan Arsitektur

Format tiap entri: tanggal, keputusan, alasan, status.
Status: `aktif` | `digantikan` | `dibatalkan`.

---

## 2026-09-12 — Struktur project berbasis dokumentasi lebih dulu
- **Keputusan:** Mulai dengan dokumentasi (`CLAUDE.md` + `docs/`) sebelum menulis
  kode aplikasi apa pun.
- **Alasan:** Product dibangun bertahap dan hemat token. Dokumentasi menjadi
  sumber konteks tunggal sehingga tidak perlu eksplorasi/penjelasan berulang.
- **Status:** aktif.

## 2026-09-12 — Belum memilih stack teknologi
- **Keputusan:** Menunda pemilihan bahasa, framework, database, penyedia AI, dan
  mekanisme Speech-to-Text.
- **Alasan:** Menghindari over-engineering dan dependency spekulatif. Stack akan
  dipilih saat task pertama yang benar-benar membutuhkannya.
- **Status:** aktif.

## 2026-09-12 — MVP dibatasi pada pencatatan cepat single-user
- **Keputusan:** MVP fokus pada alur inti `Voice/Text → AI → transaksi terstruktur
  → validasi → simpan → riwayat` untuk **satu pengguna**. Laporan mendalam,
  budgeting, multi-user, dan integrasi bank ditunda ke Phase 2/3.
- **Alasan:** Membuktikan hipotesis inti (input natural lebih cepat) tanpa
  over-engineering jadi aplikasi akunting kompleks.
- **Status:** aktif.

## 2026-09-12 — Wajib tampilkan draft transaksi sebelum simpan (MVP)
- **Keputusan:** Hasil ekstraksi AI selalu ditampilkan sebagai draft untuk
  dikonfirmasi/dikoreksi; tidak ada auto-save diam-diam di MVP.
- **Alasan:** Menjaga kepercayaan; menghindari "silent wrong" yang merusak akurasi data.
- **Status:** aktif (auto-save high-confidence dipertimbangkan Phase 2).

## 2026-09-12 — Pilihan teknis ditunda hingga Open Questions terjawab
- **Keputusan:** Platform, penyedia STT, penyedia LLM, dan strategi
  offline belum diputuskan; tercatat di `docs/PRODUCT_REQUIREMENTS.md`
  bagian OPEN PRODUCT QUESTIONS beserta rekomendasi.
- **Alasan:** Keputusan produk mendahului keputusan arsitektur; hindari asumsi besar.
- **Status:** aktif — menunggu keputusan pengguna.

## 2026-09-12 — Basis akrual & anti double-counting kartu kredit
- **Keputusan:** Expense diakui saat transaksi terjadi (basis akrual), terlepas
  dari metode bayar. Belanja pakai CC = expense + utang bertambah; **pembayaran
  tagihan CC = transfer/pelunasan liability, BUKAN expense**.
- **Alasan:** Mencegah double counting (peristiwa dihitung sekali) dan sesuai
  model mental pengguna.
- **Status:** aktif.

## 2026-09-12 — Klasifikasi akun: asset vs liability
- **Keputusan:** Cash, Bank, E-wallet = asset (saldo = uang dimiliki);
  Credit Card = liability (saldo = utang terutang). Net Worth = ΣAsset − ΣLiability.
- **Alasan:** Fondasi konsisten untuk balance, cash flow, dan net worth.
- **Status:** aktif.

## 2026-09-12 — Transaksi = sumber kebenaran, saldo = turunan
- **Keputusan:** Saldo dihitung/di-cache dari daftar transaksi, bukan disimpan
  sebagai satu-satunya sumber. Refund = contra-expense (bukan income). Transfer
  & pembayaran CC netral terhadap net worth & net cash flow.
- **Alasan:** Menjamin konsistensi saat edit/hapus dan menghindari saldo "kotor".
- **Status:** aktif.

---

<!-- Tambahkan keputusan baru di atas garis ini, entri terbaru di paling bawah bagian atas. -->
