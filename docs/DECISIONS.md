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

## 2026-09-12 — Arsitektur MVP: modular monolith, bukan microservices
- **Keputusan:** Satu backend (modular monolith) dengan modul terpisah: API,
  Validation, AI Adapter, Financial Engine, Data Access. Frontend PWA, DB SQLite
  (portabel ke Postgres). AI hanya di satu endpoint (`/nlp/parse`) di balik adapter.
- **Alasan:** Paling sederhana untuk MVP single-user; hindari kompleksitas prematur.
- **Status:** aktif.

## 2026-09-12 — AI tidak menulis DB & terpisah dari Financial Engine
- **Keputusan:** AI hanya menghasilkan draft terstruktur; penulisan hanya lewat
  validasi + konfirmasi pengguna. Financial Engine bersifat deterministik & murni,
  terpisah tegas dari AI.
- **Alasan:** Menjaga kepercayaan, testability, dan mencegah efek non-deterministik pada data keuangan.
- **Status:** aktif.

## 2026-09-12 — Model data from/to & pembayaran CC sebagai transfer
- **Keputusan:** Satu tabel `transactions` dengan `from_account_id`/`to_account_id`
  melayani semua tipe. Pembayaran kartu kredit disimpan sebagai `transfer` (bank→CC)
  sehingga otomatis bukan expense. Amount = integer rupiah > 0; arah dari tipe+peran akun.
- **Alasan:** Menegakkan anti double-counting di level data & menyederhanakan skema.
- **Status:** aktif.

## 2026-09-12 — Entity MVP dibatasi & soft delete transaksi
- **Keputusan:** MVP hanya `users, accounts, categories, transactions` (+ `ai_interactions`
  minimal opsional). `merchants`, `user_preferences`, `recurring_transactions`,
  `budgets` ditunda. Transaksi pakai soft delete; akun/kategori di-archive (RESTRICT hard delete).
- **Alasan:** Jangan buat entity sebelum diperlukan; jaga audit & konsistensi saldo turunan.
- **Status:** aktif.

## 2026-09-12 — Financial Engine diimplementasikan dengan Python, tanpa dependency
- **Keputusan:** Financial Engine (modul inti) ditulis dalam **Python 3** memakai
  **stdlib saja** (`dataclasses`, `enum`, `unittest`) — nol dependency pihak ketiga.
- **Alasan:** Modul murni/terisolasi & portabel; Python/FastAPI adalah opsi backend
  yang sudah tercatat; nol dependency = sesuai prinsip anti-over-engineering & bisa
  langsung diuji tanpa `npm install`/jaringan. Keputusan stack backend penuh (mis.
  bila memilih TypeScript) masih terbuka; engine mudah diport bila perlu.
- **Status:** aktif (dapat ditinjau ulang saat stack final ditetapkan).

## 2026-09-12 — Refund selalu dimodelkan via to_account_id
- **Keputusan:** Semua refund (ke asset maupun credit card) direkam dengan
  `to_account_id = akun tujuan` dan diperlakukan sebagai "uang kembali" — pada asset
  menambah saldo, pada CC menurunkan utang. Ini menyelaraskan implementasi dengan
  **efek** yang dinyatakan FINANCIAL_RULES #11 (refund pada CC → utang turun).
- **Alasan:** Menghindari inkonsistensi representasi kolom di FINANCIAL_RULES #3
  (yang menaruh refund-CC di `from_account_id`). Outcome finansial tidak berubah.
- **Tindak lanjut:** selaraskan tabel #3 di FINANCIAL_RULES pada revisi berikutnya.
- **Status:** aktif.

---

<!-- Tambahkan keputusan baru di atas garis ini, entri terbaru di paling bawah bagian atas. -->
