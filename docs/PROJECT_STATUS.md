# PROJECT STATUS

_Terakhir diperbarui: 2026-09-12_

## Fase Saat Ini
**Tahap 6 — AI Transaction Parser (rule-based) selesai & teruji.** Belum ada API/UI/voice/LLM nyata.

**Cara jalankan test:** `python3 -m unittest discover -s tests -t .` (stdlib, tanpa dependency). Status terakhir: **41 test OK**.

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

## Belum Dikerjakan
- [ ] **Jawab OPEN QUESTIONS** yang terkumpul (produk, finansial, arsitektur, database, UX) — blocker sebelum lapisan lain.
- [ ] **Adapter LLM nyata**: `RuleBasedParser` adalah implementasi/fallback offline; adapter LLM (provider TBD) tinggal mengimplementasikan `TransactionParser`. Menunggu keputusan provider.
- [ ] Adjustment: efek sudah didukung di engine (untuk balance), belum ada `create_adjustment` publik.
- [ ] Lapisan berikutnya (belum diminta): persistence/DB, endpoint API, voice, UI.

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
