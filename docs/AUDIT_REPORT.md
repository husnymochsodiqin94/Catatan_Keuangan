# AUDIT REPORT — MVP AI Financial Assistant

_Versi 1.0 · 2026-09-12 · Audit tahap MVP (tanpa menambah fitur)_
_Cakupan kode: `financial_engine/`, `nlp/`, `voice/`, `reporting/`, `docs/prototype/`._

Ringkasan: fondasi finansial **akurat & teruji**; ditemukan **2 defect akurasi
parser (sudah diperbaiki)**, **1 keterbatasan intent (didokumentasikan/ditunda)**,
dan **1 inefisiensi perhitungan (sudah diperbaiki)**. Aspek keamanan sebagian
besar **belum berlaku** karena belum ada server/DB/API — dicatat sebagai syarat
wajib sebelum lapisan tersebut dibangun. Kepatuhan biaya AI: **baik** (semua
aritmetika/laporan/filter deterministik, bukan AI).

Status test setelah perbaikan: **59 test OK** (`python3 -m unittest discover -s tests -t .`).

---

## 1. FINANCIAL ACCURACY — ✅ Kuat
Diuji (24 test engine + skenario kumulatif): income, expense, transfer, refund,
credit card (anti double-counting), balance, net worth, cash flow, duplicate.

| Area | Status | Bukti |
|------|--------|-------|
| income / expense | ✅ | TC-01/02 |
| transfer (netral) | ✅ | TC-03/04, total asset konstan |
| refund (contra-expense) | ✅ | TC-10/11/12 |
| credit card | ✅ | TC-05/06/07 — beli 10jt via CC + bayar CC = net worth −10jt **sekali** |
| balance / net worth | ✅ | starting + efek; soft-delete recompute (TC-17) |
| cash flow | ✅ | Income − Expense + Refund; transfer/bayar-CC dikecualikan |
| duplicate | ✅ | TC-18/19/20 — ditandai, tidak diblokir |

**Temuan:** tidak ada defect akurasi pada engine. Catatan (bukan defect):
`create_adjustment` publik belum ada (di luar lingkup); efek adjustment sudah
didukung di balance.

---

## 2. AI (Parser) — ⚠️ 2 defect diperbaiki, 1 keterbatasan ditunda
Diuji: nominal, tanggal, kategori, account, intent, ambiguous, multiple, correction.

### Diperbaiki
- **[A1 · Tinggi · akurasi] Pemisah multi-transaksi memotong frasa tanggal.**
  `SPLIT_RE` memakai `lalu` sebagai konektor, sehingga "**hari lalu**" ikut
  terpotong → tanggal & nominal salah pada kalimat seperti
  "makan 3 hari lalu pakai BCA".
  **Fix:** lookbehind `(?<!hari )\blalu\b` — "hari lalu" tidak dipecah.
  Regresi: `TestTemporalNotAmount`.
- **[A2 · Sedang · akurasi] Angka pada frasa waktu terbaca sebagai nominal.**
  Fallback angka polos menangkap "3" pada "3 hari lalu" / "9" pada "jam 9"
  ketika tak ada nominal asli.
  **Fix:** buang token waktu (`_TEMPORAL_RE`) sebelum deteksi nominal.
  Regresi: `TestTemporalNotAmount`.

### Ditunda (keterbatasan, bukan diperbaiki — perbaikan = fitur baru)
- **[A3 · Sedang · potensi double counting] Intent "bayar kartu kredit".**
  "Bayar kartu kredit 10 juta dari BCA" saat ini diklasifikasikan **expense**,
  bukan **transfer bank→CC**, karena parser belum meresolusi akun tujuan CC dari
  bahasa natural. Berpotensi double counting bila di-commit tanpa koreksi.
  **Mitigasi yang sudah ada:** langkah **konfirmasi draft** wajib; pengguna dapat
  mengoreksi tipe/akun sebelum simpan (`apply_correction`). **Rekomendasi:**
  tambah deteksi intent pembayaran CC + resolusi akun CC pada iterasi berikutnya
  (butuh daftar akun CC pengguna). Tidak dikerjakan sekarang (hindari fitur baru).

Coverage aman: nominal (ribu/rb/k, juta/jt, 1,5jt, pemisah ribuan), tanggal
(kemarin, N hari lalu, besok), kategori, account, intent (income/expense/
transfer/refund), ambiguous, multiple, correction — semua bertest.

---

## 3. SECURITY — ℹ️ Belum berlaku (belum ada server/DB/API), syarat wajib dicatat
Kode saat ini adalah **library deterministik in-memory** tanpa jaringan, tanpa
persistensi, tanpa endpoint. Karena itu banyak kontrol keamanan **belum relevan**,
tetapi WAJIB ada sebelum lapisan API/DB dibangun.

| Aspek | Kondisi MVP | Syarat sebelum API/DB |
|-------|-------------|------------------------|
| Authentication | Belum ada (single-user, tanpa login) — sesuai DECISIONS | Wajib saat multi-user / endpoint publik |
| Authorization | Belum ada | Setiap operasi ter-scope pemilik |
| User data isolation | Data in-memory satu proses | Scope `user_id`; ikuti pola `data/users/<id>` (DATABASE_DESIGN) |
| API keys | **Tidak ada** (LLM/STT belum nyata) | Simpan di env server; **jangan** pernah di klien |
| Database access | **Tidak ada DB** | Parameterized query / ORM; least-privilege |
| Input validation | ✅ Ada (engine: amount>0/int, akun ada; pipeline: schema + business) | Pertahankan di sisi server |
| Sensitive data | Hanya transaksi in-memory; tak ada PII persisted; `ai_interactions` belum ada | Enkripsi transit/at-rest; minimalkan data ke pihak ketiga |
| Error messages | ✅ Pesan Indonesia ramah, tak membocorkan internal/secret | Jangan bocorkan stack/secret ke klien |

Catatan prototipe: `docs/prototype/*.html` statis, tak mengumpulkan data & tak
memakai localStorage. Saat pakai Web Speech API nyata, audio dikirim ke layanan
STT browser — perlu disebut di kebijakan privasi saat produksi.

**Temuan:** tidak ada kerentanan aktif (tidak ada attack surface). Tidak ada
perbaikan kode yang diperlukan sekarang; daftar syarat di atas menjadi acuan
tahap API/DB.

---

## 4. PERFORMANCE — ⚠️ 1 inefisiensi diperbaiki
- **[P1 · Sedang · repeated processing] `net_worth` memindai ulang seluruh
  transaksi per akun.** `net_worth → total_assets + total_liabilities`, dan tiap
  `balance(id)` memindai semua transaksi → O(akun × transaksi) dengan `_effects`
  dibangun berulang.
  **Fix:** `_all_balances()` menghitung semua saldo dalam **satu** pindaian;
  dipakai oleh `net_worth/total_assets/total_liabilities`.
- **Catatan (tidak diperbaiki, wajar untuk MVP):** `balance(id)` tunggal masih
  O(transaksi) dan membangun `_effects` per transaksi. Untuk skala pribadi ini
  memadai; cache saldo hanya bila terbukti perlu (hindari optimasi prematur —
  sesuai DATABASE_DESIGN Open Q #4).
- **API/DB/AI call berlebih:** **tidak ada** — belum ada pemanggilan API/DB, dan
  AI (parser rule-based) dipanggil **sekali** per input; voice memanggil STT
  sekali lalu pipeline sekali. Tidak ada pemanggilan dalam loop.

---

## 5. TOKEN / AI COST — ✅ Patuh
Semua hal deterministik memakai kode, **bukan** AI:

| Kebutuhan | Implementasi | AI dipakai? |
|-----------|--------------|-------------|
| Penjumlahan/pengurangan, saldo | `financial_engine` | ❌ |
| Net worth, cash flow | `financial_engine` | ❌ |
| Laporan/dashboard (expense per kategori, recent) | `financial_engine` + `reporting` | ❌ |
| Filtering & search history | `query_transactions` (engine) + filter tampilan | ❌ |
| Perhitungan budget | (belum ada; akan deterministik) | ❌ |
| Pemahaman bahasa natural | `nlp` parser | ✅ (hanya di sini) |

AI hanya untuk NL→struktur, dipanggil sekali per input, di balik adapter, dengan
fallback rule-based. **Rekomendasi saat adapter LLM nyata ditambah:** batasi
panjang input, cache hasil identik, panggil hanya saat submit (bukan tiap
ketikan), dan pakai fallback deterministik untuk input yang jelas.

---

## 6. Ringkasan Tindakan
| ID | Area | Severity | Tindakan |
|----|------|----------|----------|
| A1 | AI/akurasi | Tinggi | ✅ Diperbaiki (splitter lookbehind) |
| A2 | AI/akurasi | Sedang | ✅ Diperbaiki (strip token waktu) |
| A3 | AI/intent | Sedang | ⏸️ Ditunda (keterbatasan; mitigasi: konfirmasi/koreksi) |
| P1 | Performance | Sedang | ✅ Diperbaiki (single-pass `_all_balances`) |
| SEC | Security | Info | 📋 Syarat dicatat untuk tahap API/DB (tak ada surface sekarang) |

Test regresi ditambahkan (`TestTemporalNotAmount`); total suite **59 test OK**.
