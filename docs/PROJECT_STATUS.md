# PROJECT STATUS

_Terakhir diperbarui: 2026-09-12_

## Fase Saat Ini
**Tahap 12 — Fitur lengkap MVP+: budget/target/alert, edit, auth opsional, layout desktop.** PWA + backend Python stdlib + SQLite. Smoke-test end-to-end OK.

Berfungsi: capture (suara/teks) → parse → konfirmasi → simpan; dashboard; riwayat (search/filter/**edit**/hapus); **Anggaran** (batas pengeluaran & target pemasukan per hari/minggu/bulan, anggaran per kategori, status & alert); **banner alert** di Beranda; **auth token opsional** (`CATATAN_TOKEN`) & **alert email** (`SMTP_*`) untuk deploy; **layout desktop** (sidebar) responsif. Semua angka dari engine.

**Cara jalankan:** `python3 -m server.app` → http://127.0.0.1:8000. Deploy & env: `docs/DEPLOY.md`.
**Cara jalankan test:** `python3 -m unittest discover -s tests -t .` (stdlib, tanpa dependency). Status terakhir: **87 test OK**.

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
- [x] **Arsip & Pindah-lalu-hapus Akun**: (a) **Arsipkan** akun (`PATCH archived:true`) — disembunyikan dari dropdown transaksi & chip Beranda, tidak bisa dipakai transaksi baru (guard engine), tampil di bagian "Diarsipkan" dengan tombol Aktifkan kembali. (b) **Pindahkan transaksi lalu hapus** (`DELETE /api/accounts/{id}?move_to={targetId}`) — semua transaksi di-reassign ke akun tujuan (transfer yang jadi ke-diri-sendiri di-soft-delete) lalu akun dihapus. UI: sheet "Hapus / Arsipkan Akun" dengan pilihan Arsipkan, Pindahkan & Hapus (dropdown akun tujuan), atau Hapus permanen. Service worker `ck-shell-v3`. **87 test OK**.
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
