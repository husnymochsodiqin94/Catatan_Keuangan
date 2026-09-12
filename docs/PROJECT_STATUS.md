# PROJECT STATUS

_Terakhir diperbarui: 2026-09-12_

## Fase Saat Ini
**Tahap 10 — Mockup UI (design canvas) untuk PWA.** Keputusan platform: **PWA** (mobile + web + laptop, satu basis kode). Belum ada aplikasi/API/DB nyata.

**Mockup (design canvas, Versi 4):** 9 artboard — Home, Capture, Konfirmasi, Riwayat, Anggaran per kategori, **Akun (aset/liabilitas/utang-piutang)**, **Statistik (donat + tren)**, **Target & Batas + Alert WhatsApp**, dan tampilan Web/Laptop. (File kerja di scratchpad sesi; canvas tersimpan sebagai Artifact.)

**Cara jalankan test:** `python3 -m unittest discover -s tests -t .` (stdlib, tanpa dependency). Status terakhir: **59 test OK**.
**Regenerate dashboard demo:** `python3 -m reporting.render_demo` → `docs/prototype/dashboard.html`.

## Roadmap Fitur (dari masukan user, 2026-09-12)
- **Sudah ada di engine (tinggal disambungkan ke UI):** transfer antar akun, e-wallet, kartu kredit/liabilitas (utang dasar).
- **Prioritas Phase 2 (butuh engine + DB):** Budgeting per kategori + notifikasi 80–100% (prioritas tertinggi), **batas pengeluaran & target pemasukan per periode (harian/mingguan/bulanan) + ambang alert 90%**, recurring/upcoming bills otomatis, tren MoM, filter periode custom, export CSV/Excel/PDF, utang/piutang eksplisit.
- **Alert WhatsApp (Phase 2, integrasi eksternal):** butuh backend + provider (WhatsApp Business Cloud API/Meta atau Twilio) + template pesan + verifikasi nomor + pemicu. Notifikasi in-app bisa lebih dulu (lebih murah). Logika ambang = deterministik di engine.
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
