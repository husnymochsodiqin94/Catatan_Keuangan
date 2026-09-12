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

## 2026-09-12 — AI Parser diimplementasikan sebagai adapter rule-based (LLM ditunda)
- **Keputusan:** Parser NL→transaksi dibangun di balik antarmuka `TransactionParser`.
  Implementasi awal `RuleBasedParser` bersifat deterministik & offline (tanpa
  dependency/LLM). Adapter berbasis LLM (provider TBD) akan mengimplementasikan
  antarmuka yang sama tanpa mengubah pipeline.
- **Alasan:** Provider LLM masih Open Question & tak ada API key; rule-based dapat
  diuji deterministik, menjadi fallback, dan menegakkan boundary arsitektur.
- **Status:** aktif (adapter LLM menyusul setelah provider dipilih).

## 2026-09-12 — Boundary: output parser tidak pernah langsung ke DB
- **Keputusan:** Pipeline menegakkan `parse → schema validation → business
  validation → Financial Engine`. Parser hanya menghasilkan `Draft`; penyimpanan
  hanya lewat `commit(draft)` eksplisit untuk draft berstatus READY. Draft
  INCOMPLETE/AMBIGUOUS/NOT_TRANSACTION tidak bisa di-commit. Duplikat ditandai
  (bukan diblokir); `commit(allow_duplicate=False)` menolak sampai dikonfirmasi.
- **Alasan:** Konsisten dengan prinsip "draft dulu" & memisahkan AI probabilistik
  dari Financial Engine deterministik.
- **Status:** aktif.

## 2026-09-12 — Voice konvergen ke teks & memakai pipeline yang sama
- **Keputusan:** Voice input = STT → teks → `ParsePipeline` yang identik dengan
  text input. STT di balik antarmuka `SpeechToText` (fake untuk test; browser Web
  Speech API di prototipe; provider nyata menyusul). Tidak ada logika parsing
  khusus voice, sehingga hasil suara = hasil mengetik kalimat yang sama.
- **Alasan:** Menjamin parity voice=teks, menghindari duplikasi logika, hemat
  pemeliharaan. Financial Engine tidak diubah.
- **Status:** aktif.

## 2026-09-12 — Fallback voice: selalu ada jalur teks manual
- **Keputusan:** Bila STT gagal/kosong/error → `VoiceResult(fallback=True)` dan UX
  mengarahkan ke input teks manual. STT low-confidence tetap di-parse namun
  ditandai untuk direview/diedit sebelum simpan.
- **Alasan:** Prioritas error handling & UX sederhana; suara tidak boleh menjadi
  jalan buntu.
- **Status:** aktif.

## 2026-09-12 — Angka UI hanya dari Financial Engine (satu sumber kebenaran)
- **Keputusan:** Agregasi dashboard (ringkasan bulan, expense per kategori) &
  query history (filter/search/edit) berada di **financial layer** (method engine:
  `month_summary`, `expense_by_category`, `query_transactions`,
  `recent_transactions`, `edit_transaction`). Lapisan `reporting/` hanya memetakan
  & memformat; renderer HTML hanya menampilkan data yang disematkan. Frontend
  boleh memfilter/mencari baris (presentasi) tetapi TIDAK menghitung ulang angka finansial.
- **Alasan:** Mencegah logika finansial ganda/menyimpang di frontend; konsisten
  dengan "transaksi = sumber kebenaran, saldo = turunan".
- **Status:** aktif.

## 2026-09-12 — Platform: PWA (mobile + web + laptop), mockup dulu
- **Keputusan:** Aplikasi dibangun sebagai **PWA** (satu basis kode React untuk
  HP, web, dan laptop), sesuai rekomendasi arsitektur. Tahap desain dimulai
  dengan mockup (design canvas) sebelum coding.
- **Alasan:** Memenuhi "mobile + web + laptop" dengan satu basis kode, hemat, bisa
  masuk Play Store belakangan via TWA.
- **Status:** aktif.

## 2026-09-12 — Prioritas fitur pasca-MVP (masukan user)
- **Keputusan:** Budgeting per kategori (+notifikasi 80–100%) dijadikan
  prioritas Phase 2 tertinggi; menyusul recurring/upcoming bills, tren MoM,
  filter periode custom, export data, utang/piutang eksplisit. Multi-currency
  = Phase 3. Transfer/e-wallet/liabilitas sudah ada di engine.
- **Alasan:** Fitur yang paling dicari pengguna; tetap dijaga bertahap agar tidak
  over-engineering di MVP.
- **Status:** aktif (ditampilkan sebagai mockup, implementasi menyusul).

## 2026-09-12 — Channel alert: Email dulu, WhatsApp ditunda
- **Keputusan:** Channel pengiriman alert untuk saat ini = **Email** (+ notifikasi
  in-app). **WhatsApp ditunda** (tetap di roadmap, ditandai "Segera · Phase 2").
- **Alasan:** Email jauh lebih sederhana — cukup penyedia SMTP/email (mis.
  Amazon SES / SendGrid / Resend), tanpa template approval Meta atau verifikasi
  nomor bisnis. Tetap butuh backend untuk mengirim, tetapi hambatannya kecil.
- **Status:** aktif (UI mockup sudah email-first; implementasi menyusul saat backend ada).

## 2026-09-12 — Target/Batas per periode + alert; WhatsApp butuh backend (Phase 2)
- **Keputusan:** Fitur set **batas pengeluaran** & **target pemasukan** per
  Harian/Mingguan/Bulanan + **ambang alert** (default 90%). Logika ambang =
  deterministik di Financial Engine (bandingkan akumulasi periode vs batas).
  Pengiriman **WhatsApp** memerlukan backend + provider (WhatsApp Business Cloud
  API/Meta atau Twilio) + template pesan disetujui + verifikasi nomor + pemicu
  (saat transaksi disimpan / cek terjadwal) → **Phase 2**, tidak berfungsi di
  fase mockup. Channel alternatif: notifikasi in-app (paling murah, bisa lebih dulu).
- **Alasan:** Pisahkan logika deterministik (murah, bisa diuji) dari integrasi
  eksternal (butuh infra & kredensial); hindari over-promise di tahap mockup.
- **Status:** aktif — UI sudah dimock (layar "Target & Batas"); implementasi menyusul.

## 2026-09-12 — Backend & PWA tanpa dependency pihak ketiga
- **Keputusan:** Backend memakai **Python stdlib** (`http.server` + `sqlite3`),
  bukan FastAPI; frontend **PWA statis** (HTML/CSS/JS) tanpa build step/npm.
  Backend menyajikan API JSON + file PWA di satu origin.
- **Alasan:** Mempertahankan prinsip nol-dependency yang sudah dijaga (engine/nlp/
  voice/reporting semuanya stdlib), bisa langsung dijalankan tanpa install/jaringan,
  dan cukup untuk skala pribadi (single-user). FastAPI/React+Vite dapat diadopsi
  nanti bila kebutuhan tumbuh.
- **Status:** aktif.

## 2026-09-12 — Persistensi: transaksi = sumber kebenaran, engine direhidrasi
- **Keputusan:** Storage SQLite hanya menyimpan akun & transaksi mentah. Tiap
  operasi merehidrasi `FinancialEngine` dari storage, memakainya untuk validasi &
  perhitungan (saldo/laporan), lalu menyimpan hasilnya. Tidak ada logika finansial
  yang diduplikasi di server/frontend; frontend hanya menampilkan angka dari API.
- **Alasan:** Menjaga satu sumber kebenaran & konsistensi (edit/hapus otomatis benar).
- **Status:** aktif.

## 2026-09-12 — Budget/target/alert = logika deterministik di engine
- **Keputusan:** Evaluasi batas pengeluaran, target pemasukan (per hari/minggu/
  bulan), anggaran per kategori, dan ambang alert ada di `financial_engine/
  budgeting.py` (murni, memakai cash_flow/expense_by_category). Pengaturan
  disimpan sebagai JSON di tabel `settings`. Alert dihasilkan sebagai daftar
  siap-kirim; pengiriman email terpisah (adapter).
- **Alasan:** Konsisten — semua perhitungan finansial deterministik & teruji,
  bukan di frontend.
- **Status:** aktif.

## 2026-09-12 — Alert email via adapter tergated env; auth token opsional
- **Keputusan:** Email dikirim lewat `server/email_alert.py` (smtplib stdlib),
  aktif hanya bila `SMTP_HOST`+`SMTP_FROM` diset; jika tidak, alert in-app saja.
  Auth diaktifkan dengan menyetel `CATATAN_TOKEN` (API butuh token); default lokal
  tanpa auth. Deploy didokumentasikan di `docs/DEPLOY.md`.
- **Alasan:** Menjaga app bisa jalan tanpa konfigurasi (lokal) namun siap di-deploy
  aman; hindari dependency & kredensial wajib di MVP.
- **Status:** aktif (WhatsApp tetap ditunda; multi-user/login proper menyusul).

---

<!-- Tambahkan keputusan baru di atas garis ini, entri terbaru di paling bawah bagian atas. -->
