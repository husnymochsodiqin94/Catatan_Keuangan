# PROJECT STATUS

_Terakhir diperbarui: 2026-09-12_

## Fase Saat Ini
**Tahap 12 — Fitur lengkap MVP+: budget/target/alert, edit, auth opsional, layout desktop.** PWA + backend Python stdlib + SQLite. Smoke-test end-to-end OK.

Berfungsi: capture (suara/teks) → parse → konfirmasi → simpan; dashboard; riwayat (search/filter/**edit**/hapus); **Anggaran** (batas pengeluaran & target pemasukan per hari/minggu/bulan, anggaran per kategori, status & alert); **banner alert** di Beranda; **auth token opsional** (`CATATAN_TOKEN`) & **alert email** (`SMTP_*`) untuk deploy; **layout desktop** (sidebar) responsif. Semua angka dari engine.

**Cara jalankan:** `python3 -m server.app` → http://127.0.0.1:8000. Deploy & env: `docs/DEPLOY.md`.
**Cara jalankan test:** `python3 -m unittest discover -s tests -t .` (stdlib, tanpa dependency). Status terakhir: **96 test OK**.

## Roadmap Fitur (dari masukan user, 2026-09-12)
- **Sudah ada di engine (tinggal disambungkan ke UI):** transfer antar akun, e-wallet, kartu kredit/liabilitas (utang dasar).
- **Prioritas Phase 2 (butuh engine + DB):** Budgeting per kategori + notifikasi 80–100% (prioritas tertinggi), **batas pengeluaran & target pemasukan per periode (harian/mingguan/bulanan) + ambang alert 90%**, recurring/upcoming bills otomatis, tren MoM, filter periode custom, export CSV/Excel/PDF, utang/piutang eksplisit.
- **Alert channel (Phase 2):** **Email dulu** (butuh penyedia SMTP/email spt SES/SendGrid/Resend — relatif sederhana) + notifikasi in-app. **WhatsApp ditunda** (butuh WhatsApp Business Cloud API/Meta atau Twilio + template + verifikasi nomor). Logika ambang = deterministik di engine; pemicu saat transaksi disimpan / cek terjadwal.
- **Phase 3:** Multi-currency.
- Elemen di atas sudah ditampilkan sebagai **mockup** (belum berfungsi) untuk memvalidasi arah UI.

## Sudah Dikerjakan
- [x] Inisialisasi repository git (branch `claude/financial-assistant-setup-n1aqkd`).
- [x] Struktur dasar project minimal (folder `docs/`, `.gitignore`, `README.md`).
- [x] `CLAUDE.md` — aturan utama project.
- [x] `docs/PRODUCT_VISION.md` — visi & lingkup produk.
- [x] `docs/DECISIONS.md` — catatan keputusan.
- [x] `docs/PROJECT_STATUS.md` — file ini.
- [x] `docs/PRODUCT_REQUIREMENTS.md` — definisi produk (Tahap 1: problem, persona, JTBD, flow, requirement, MVP/Phase, metrik, risiko, edge cases, open questions).
- [x] `docs/FINANCIAL_RULES.md` — aturan keuangan (Tahap 2: income/expense/transfer/refund/adjustment, tipe akun, formula balance/cash flow/net worth, anti double-counting CC, duplikat, contoh, edge cases, test cases).
- [x] `docs/SYSTEM_ARCHITECTURE.md` — arsitektur MVP (Tahap 3: modular monolith, komponen, data flow, API/AI/financial/security boundary, rekomendasi teknologi, trade-offs).
- [x] `docs/DATABASE_DESIGN.md` — desain DB MVP (Tahap 3: evaluasi entity, ERD, field/PK/FK/index/constraint, pemetaan tipe transaksi ke from/to, deletion & audit).
- [x] `docs/UX_UI_MVP.md` — desain UX MVP (Tahap 4: IA, screen hierarchy, user flow, komponen, UI states, spesifikasi layar, microcopy).
- [x] `docs/prototype/index.html` — prototipe UX statis alur inti Capture→Preview→Simpan (parser tiruan, tanpa backend/AI).
- [x] **Financial Engine** (`financial_engine/`): create income/expense/transfer/refund, balance, cash flow, net worth, validasi transaksi, deteksi duplikat. Python, tanpa dependency.
- [x] **Test** (`tests/test_financial_engine.py`): income, expense, transfer, refund, balance, multiple accounts, credit card (anti double-counting), duplikat, validasi. 24 test OK.
- [x] **AI Transaction Parser** (`nlp/`): schema `ParsedTransaction` + `validate_schema`; antarmuka `TransactionParser` + `RuleBasedParser` (deterministik, id-ID); `ParsePipeline` (parse → schema → business validation → siap ke Financial Engine, tanpa persistensi; `commit()` eksplisit, `apply_correction()`).
- [x] **Test** (`tests/test_nlp_parser.py`): expense, income, transfer, multiple, natural date, nominal Indonesia, missing account, ambiguous/bukan-transaksi, correction, duplicate. 17 test OK.
- [x] **Voice input** (`voice/`): antarmuka `SpeechToText` + `FakeSpeechToText`; `VoiceInputHandler` (STT → `ParsePipeline` yang sama dengan teks → drafts; fallback bila STT gagal/kosong/error; low-confidence minta review). Prototipe (`docs/prototype/index.html`) memakai Web Speech API (id-ID) dengan fallback ke ketik manual.
- [x] **Test** (`tests/test_voice_input.py`): parity voice=teks ("Beli makan siang 50 ribu pakai BCA"), tidak auto-simpan, STT gagal/kosong/exception → fallback, low-confidence → review. 6 test OK.
- [x] **Reporting/UI** (`reporting/`, `financial_engine` +method): Dashboard (total balance, income/expense/net cash flow bulan ini, expense per kategori, recent) & Transaction History (list, filter, search, edit, delete) — **semua angka dari Financial Engine** (`month_summary`, `expense_by_category`, `query_transactions`, `recent_transactions`, `edit_transaction`). Renderer HTML hanya menampilkan data (`docs/prototype/dashboard.html`) + loading/empty/error state.
- [x] **Test** (`tests/test_reporting.py`): angka dashboard = engine, expense-per-kategori neto & terurut, recent, filter/search/account, edit & delete memengaruhi saldo/dashboard. 9 test OK.
- [x] **Backend** (`server/`): Storage SQLite (stdlib) + service (rehidrasi engine, validasi, simpan) + HTTP server (API JSON `/api/accounts|parse|transactions|summary` + penyajian PWA). Nol dependency pihak ketiga.
- [x] **PWA** (`webapp/`): index/app.js/styles + manifest + service worker; Home/Riwayat/Akun + capture (Web Speech id-ID + teks) → parse → confirm → simpan; onboarding & error/loading state; semua angka dari backend.
- [x] **Test** (`tests/test_server.py`): akun, parse, commit+persist, transfer, delete, persistensi, settings, budget status, edit, alerts. 12 test OK.
- [x] **Budgeting** (`financial_engine/budgeting.py`): batas pengeluaran & target pemasukan per periode (harian/mingguan/bulanan), anggaran per kategori, evaluasi ambang & daftar alert (deterministik). Test `tests/test_budgeting.py` (7 OK).
- [x] **Alert email** (`server/email_alert.py`): pengiriman via SMTP (stdlib), aktif bila dikonfigurasi (`SMTP_*`); jika tidak, alert in-app.
- [x] **Auth opsional** (`CATATAN_TOKEN`) & **panduan deploy** (`docs/DEPLOY.md`).
- [x] **Artefak deploy**: `Dockerfile` (python:3.11-slim, healthcheck), `docker-compose.yml` (app + Caddy HTTPS otomatis), `deploy/Caddyfile`, `deploy/catatan.service` (systemd), `.env.example`, `.dockerignore`, `deploy/setup.sh` + `docs/DEPLOY_ORACLE.md` (deploy gratis Oracle+DuckDNS). Diverifikasi berjalan dari salinan berisi hanya paket app.
- [x] **Restyle PWA sesuai mockup (tema terang)**: font Inter, aksen emerald `#10B981` + cyan `#06B6D4`, kartu Total Saldo gradient + chips per-akun, kartu "Keluar + Terbesar", animasi waveform saat merekam. Service worker network-first agar update langsung tampil.
- [x] **Autentikasi multi-user (email + password)**: `server/auth.py` (PBKDF2 stdlib), tabel `users`/`sessions`, data **terisolasi per user** (accounts/transactions/settings ber-`user_id`). Endpoint `/api/auth/register|login|logout|me`, sesi via token `X-Token`. Frontend: layar **Login/Daftar**, tombol **Keluar** di menu Akun.
- [x] **Dashboard & Draft gaya mockup (tema terang)**: Beranda (kartu Total Saldo + rincian akun, kartu Pengeluaran + mini bar chart + Terbesar, transaksi beravatar, ikon gear/bell). Kartu **Draft Transaksi** dengan **dropdown Kategori & Akun**, tombol KONFIRMASI & SIMPAN.
- [x] **Edit & Hapus Akun**: `PATCH/DELETE /api/accounts/{id}` (nama/tipe/saldo awal), guard menolak hapus akun yang masih punya transaksi & akun milik user lain. UI: tombol ubah/hapus di daftar Akun.
- [x] **Arsip & Pindah-lalu-hapus Akun**: (a) **Arsipkan** akun (`PATCH archived:true`) — disembunyikan dari dropdown transaksi & chip Beranda, tidak bisa dipakai transaksi baru (guard engine), tampil di bagian "Diarsipkan" dengan tombol Aktifkan kembali. (b) **Pindahkan transaksi lalu hapus** (`DELETE /api/accounts/{id}?move_to={targetId}`) — semua transaksi di-reassign ke akun tujuan (transfer yang jadi ke-diri-sendiri di-soft-delete) lalu akun dihapus. UI: sheet "Hapus / Arsipkan Akun" dengan pilihan Arsipkan, Pindahkan & Hapus (dropdown akun tujuan), atau Hapus permanen. **87 test OK**.
- [x] **Perbaikan migrasi DB lama**: index `user_id` dibuat setelah `_migrate()`, dan `_migrate()` menambal kolom `user_id`+`archived` yang belum ada — mengatasi `no such column: user_id` pada DB single-user lama.
- [x] **Pemisah ribuan pada input angka** (id-ID, mis. `10.000.000`): semua field nominal/saldo/batas (bukan persen) memformat otomatis saat diketik via kelas `.money`; nilai tetap dibaca sebagai integer di backend.
- [x] **Transaksi berulang + pengingat (Tahap C)**: tagihan berulang disimpan di settings (`recurring`: nama, nominal, tanggal jatuh tempo, jenis, kategori, akun). `service.upcoming_bills` menghitung jatuh tempo berikut (deterministik), `budget_status` menambah **pengingat H-3** ke alerts + daftar `upcoming`. UI: kelola di **Anggaran** (tambah/hapus), kartu **Tagihan Mendatang** + tombol **Catat** di Beranda (catat manual, aman tanpa auto-post).
- [x] **Target Tabungan / Goals (Tahap D)**: goals disimpan di settings (nama, target, terkumpul). UI di **Anggaran**: daftar dengan progress bar, **+ Tambah dana**, hapus. SW `ck-shell-v13`.
- [x] **Layar Laporan (Insight) + Ekspor CSV**: `GET /api/reports` (tren 6 bulan masuk/keluar/net, rincian kategori bulan berjalan, rata-rata pengeluaran) — semua dari engine. Layar **Laporan** (ikon grafik di Beranda): bar chart tren + kartu rata-rata + kategori berperingkat. **Ekspor CSV** (`GET /api/transactions/export`, auth via X-Token, unduh via blob) dari Riwayat & Laporan. SW `ck-shell-v12`.
- [x] **Audit lanjutan — perbaikan keamanan & robustness**:
  - **2FA aman di produksi**: kode OTP TIDAK lagi dikembalikan di respons secara default. Hanya dikirim via email bila SMTP dikonfigurasi; kode dev hanya tampil jika `CATATAN_2FA_DEV=1` (uji lokal). Bila tak bisa kirim, 2FA dilewati (tanpa membocorkan kode).
  - **Kedaluwarsa sesi** 30 hari (`SESSION_TTL_DAYS`) — sesi lama otomatis invalid.
  - **Rate-limit login & OTP** anti brute-force (8 percobaan / 15 menit, in-memory + lock).
  - **SQLite WAL + busy_timeout** — aman untuk akses banyak thread, hindari "database is locked".
  - **Skrip backup** `deploy/backup.sh` (rotasi 14 salinan, `.backup` konsisten) + panduan cron harian.
- [x] **Audit lanjutan — perbaikan parser nominal**: dukung **miliar/milyar**, **"koma" desimal** ("1 koma 5 juta"), **penjumlahan magnitudo** ("2 juta 500 ribu"), typo **rebu**, dan **angka bentuk kata** ("lima puluh ribu") sebagai fallback. Verifikasi edge-case.
- [x] **QA end-to-end + fix bug nominal suara**: STT kadang menuliskan angka sebagai KATA ("lima puluh ribu") — parser dulu hanya paham digit, sehingga nominal "kadang masuk kadang tidak". Ditambah parser **angka kata Indonesia** (`_words_to_amount`: satu…sembilan, belas, puluh, ratus, ribu/juta/miliar, se-, setengah) sebagai fallback; digit tetap jalur utama; butuh kata skala agar "satu/dua" biasa tak jadi nominal. Verifikasi E2E di service (register→akun→parse nominal kata & tanggal→simpan→dashboard→edit/hapus→duplikat→budget/safe-to-spend→arsip/pindah-hapus→isolasi user): **24/24 lulus**. **101 test OK**.
- [x] **Persiapan rilis mobile / Play Store**: ikon PNG brand emerald→cyan (`icon-192/512/maskable-512.png`, dibuat via generator stdlib), `manifest.webmanifest` dirapikan (theme `#10B981`, orientation, categories, ikon PNG + maskable), meta `apple-mobile-web-app-*` + `theme-color` di `index.html`, ikon di-cache SW (`ck-shell-v11`). Panduan lengkap `docs/PUBLISH_PLAYSTORE.md` (jalur TWA via PWABuilder/Bubblewrap, Digital Asset Links, langkah Play Console). Prasyarat: deploy online HTTPS.
- [x] **Parser tanggal eksplisit**: nama bulan Indonesia ("25 agustus 2026"), numerik ("25/08/2026"), "tanggal 25" (bulan berjalan); angka tanggal tak jadi nominal; tanpa tanggal = hari ini.
- [x] **Fase 1 fitur PRD lanjutan** (dari dokumen usulan user):
  - **2FA email per 14 hari**: setelah email+password benar, bila verifikasi terakhir >14 hari, sistem mengirim **kode OTP 6 digit** ke email (SMTP stdlib; bila SMTP belum dikonfigurasi, kode dev ditampilkan agar tetap bisa masuk lokal). Endpoint `POST /api/auth/2fa/verify`; kolom `users.last_2fa_at` + tabel `twofa_codes` (OTP di-hash SHA-256, TTL 10 menit). Layar **Verifikasi Masuk** di frontend.
  - **Duplicate Protection (≤5 menit)**: saat menyimpan, transaksi dengan nominal+akun sama & **kategori identik** dalam 5 menit dikembalikan sebagai `{duplicate}` (belum tersimpan) → pop-up konfirmasi "catat lagi / batalkan"; konfirmasi mengirim ulang `allow_duplicate`.
  - **Safe-to-Spend harian**: `budgeting.evaluate` menambah `safe_to_spend` = sisa batas bulanan / sisa hari bulan berjalan (0 bila over). Ditampilkan sebagai kartu di **Anggaran**.
- [x] **Taksonomi kategori (listing)** `nlp/taxonomy.py` — sumber kebenaran tunggal: 3 kategori Pemasukan + 8 kategori Pengeluaran, masing-masing dengan subkategori & keyword (dari dokumen taksonomi user). Parser rule-based memakai keyword untuk mengisi kategori/subkategori dan **menentukan tipe dari grup kategori** (mis. "dividen" → income). Endpoint publik `GET /api/categories` menyajikan listing terkelompok. Dropdown Kategori di draft kini **berkelompok (`optgroup`) per kategori utama + subkategori**, tersaring sesuai jenis (pemasukan/pengeluaran). Perbaikan regresi: kata kunci tipe (transfer/refund/income/expense) dicocokkan **per-kata** agar "tf" tak salah cocok di "ne**tf**lix". Service worker `ck-shell-v5`. **91 test OK**.
- [x] **Audit MVP** (`docs/AUDIT_REPORT.md`): financial accuracy, AI, security, performance, token/AI-cost. Defect diperbaiki: A1 splitter "hari lalu", A2 angka frasa waktu jadi nominal, P1 repeated processing di `net_worth`. Regresi `TestTemporalNotAmount` ditambahkan.

## Temuan Audit Terbuka (belum dikerjakan — bukan defect diam-diam)
- [ ] **A3** — Intent "bayar kartu kredit ... dari BCA" belum dikenali sebagai transfer bank→CC (potensi double counting bila di-commit tanpa koreksi). Mitigasi: konfirmasi/koreksi draft. Perbaikan = fitur baru (butuh resolusi akun CC).
- [ ] **SEC** — Auth, authorization, user isolation, API keys, DB access wajib diimplementasikan **sebelum** lapisan API/DB (saat ini belum ada attack surface).

## Belum Dikerjakan
- [ ] **Jawab OPEN QUESTIONS** yang terkumpul (produk, finansial, arsitektur, database, UX) — blocker sebelum lapisan lain.
- [ ] **Adapter nyata**: `RuleBasedParser` (parser) & `SpeechToText` (voice) masih pakai implementasi rule-based/fake; adapter LLM & STT provider nyata tinggal mengimplementasikan antarmuka yang sama. Menunggu keputusan provider.
- [ ] Adjustment: efek sudah didukung di engine (untuk balance), belum ada `create_adjustment` publik.
- [ ] Lapisan berikutnya (belum diminta): persistence/DB, endpoint API, UI penuh.

## Catatan Konsistensi Aturan (perlu perhatian, tidak memblokir)
- `FINANCIAL_RULES.md` #3 menaruh "refund ke credit card" pada kolom `from_account_id`,
  sedangkan formula #11 menyatakan efeknya **menurunkan utang** (−amount). Engine
  mengikuti **efek** yang benar (utang turun) dengan memodelkan refund selalu via
  `to_account_id`. Outcome tidak berubah; hanya representasi kolom di #3 yang perlu
  diselaraskan agar konsisten dengan #11.
- [ ] Pemilihan stack teknologi (bahasa/framework).
- [ ] Desain model data transaksi.
- [ ] Pemilihan penyedia model AI untuk ekstraksi entitas.
- [ ] Pemilihan mekanisme input suara (Speech-to-Text).
- [ ] Skema penyimpanan / database.
- [ ] Antarmuka pengguna (UI).
- [ ] Logika inti: input natural → ekstraksi → simpan transaksi.

## Catatan
- Semua item "Belum Dikerjakan" menunggu instruksi eksplisit. Jangan dikerjakan
  sebelum diminta.
- Setiap keputusan teknis baru dicatat di `docs/DECISIONS.md`.

## Progress Aktif (jika berhenti di tengah task)
_Kosong — tidak ada task yang tergantung._
