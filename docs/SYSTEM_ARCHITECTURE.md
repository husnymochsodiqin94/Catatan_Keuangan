# SYSTEM ARCHITECTURE — AI Financial Assistant

_Versi 1.0 · 2026-09-12 · Tahap 3: System Architecture_
_Perspektif Senior System Architect. Arsitektur **paling sederhana** yang
memenuhi MVP. Tanpa kode, tanpa microservices, tanpa abstraksi hipotetis._

> Alur inti (dari FINANCIAL_RULES & PRODUCT_REQUIREMENTS):
> `Voice/Text → AI parse → draft terstruktur → validasi → konfirmasi → Financial Engine → Database`.

---

## 1. Prinsip Arsitektur
- **Modular monolith**, bukan microservices. Satu backend, modul terpisah secara logis.
- **Deterministik dipisah dari non-deterministik:** Financial Engine (deterministik,
  teruji) terpisah tegas dari AI layer (probabilistik).
- **Transaksi = sumber kebenaran; saldo = turunan** (sesuai DECISIONS).
- **AI tidak pernah menulis langsung ke DB.** AI hanya menghasilkan *draft*;
  penulisan hanya lewat validasi + konfirmasi.
- **Tanpa dependency spekulatif.** Tambah komponen hanya saat fase membutuhkannya.

## 2. Architecture Diagram (MVP)

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT (PWA / mobile-web)                 │
│  - Input suara → teks (Web Speech API browser, MVP)           │
│  - Input teks                                                 │
│  - Tampilkan DRAFT transaksi → konfirmasi/koreksi             │
│  - Riwayat & ringkasan                                        │
└───────────────▲───────────────────────────┬──────────────────┘
                │ HTTPS (REST/JSON)          │
                │                            ▼
┌───────────────┴───────────────────────────────────────────────┐
│                      BACKEND (modular monolith)                 │
│                                                                 │
│  [API Layer]  REST endpoints, auth, request/response           │
│       │                                                         │
│       ▼                                                         │
│  [Validation Layer]                                             │
│    (1) Schema validation  (2) Business/financial validation     │
│       │                                                         │
│       ├──────────────► [AI Adapter] ──► LLM provider (extern)   │
│       │                (parse teks → draft JSON, TIDAK simpan)  │
│       │                                                         │
│       ▼                                                         │
│  [Financial Engine]  (deterministik, murni)                    │
│    - terapkan aturan tipe transaksi                             │
│    - hitung balance / net cash flow / net worth                 │
│    - deteksi duplikat, cegah double counting CC                 │
│       │                                                         │
│       ▼                                                         │
│  [Data Access Layer]                                            │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
                 ┌────────────────────┐
                 │  DATABASE (SQLite   │
                 │  MVP → Postgres)    │
                 └────────────────────┘
```

## 3. Komponen & Tanggung Jawab

| Komponen | Tanggung jawab | MVP? |
|----------|----------------|------|
| **Frontend** | Input teks/suara, tampilkan draft, konfirmasi/koreksi, riwayat, ringkasan | ✅ |
| **Voice layer** | Speech-to-Text di sisi klien (Web Speech API browser) → teks | ✅ (MVP hemat) |
| **API layer** | Endpoint REST, auth, serialisasi | ✅ |
| **Validation layer** | Validasi skema + validasi bisnis (aturan finansial, duplikat) | ✅ |
| **AI layer (adapter)** | Teks → draft transaksi terstruktur (JSON), skor confidence | ✅ |
| **Financial engine** | Terapkan aturan FINANCIAL_RULES, hitung saldo & laporan | ✅ |
| **Data access** | Baca/tulis entity, transaksi DB | ✅ |
| **Database** | Penyimpanan persisten | ✅ |
| **Auth** | Identitas & kepemilikan data | ✅ (minimal) |

## 4. Data Flow (pencatatan satu transaksi)
1. Klien mengirim teks (hasil ketik atau STT) ke `POST /nlp/parse`.
2. **AI Adapter** memanggil LLM (output JSON terstruktur) → draft transaksi + confidence.
3. **Validation layer** memeriksa skema draft (field, tipe, nominal > 0).
4. Backend mengembalikan draft ke klien (**belum disimpan**).
5. Klien menampilkan draft; pengguna **konfirmasi/koreksi**.
6. Klien mengirim transaksi final ke `POST /transactions`.
7. **Validation layer** menjalankan validasi bisnis (akun ada, aturan tipe,
   cek duplikat via Financial Engine).
8. **Financial Engine** menerapkan aturan & (opsional) memperbarui saldo turunan.
9. **Data access** menyimpan transaksi. Respons: transaksi tersimpan + ringkasan.

> Laporan (`GET /reports/summary`) dihitung Financial Engine dari transaksi,
> bukan dari nilai saldo yang disimpan mentah.

## 5. API Boundary (MVP, indikatif)
Semua endpoint di bawah kepemilikan `user_id` (dari auth).

| Method | Path | Fungsi |
|--------|------|--------|
| POST | `/nlp/parse` | Teks → draft transaksi (AI). **Tidak menyimpan.** |
| POST | `/transactions` | Simpan transaksi (setelah konfirmasi). |
| GET | `/transactions` | Daftar/riwayat (filter periode/akun). |
| PATCH | `/transactions/:id` | Edit transaksi. |
| DELETE | `/transactions/:id` | Hapus (soft delete). |
| GET | `/accounts` · POST `/accounts` | Kelola akun. |
| GET | `/categories` | Daftar kategori (default + kustom nanti). |
| GET | `/reports/summary` | Net cash flow, net worth, saldo per akun. |

**Kontrak:** `/nlp/parse` adalah satu-satunya endpoint yang menyentuh AI.
Endpoint tulis transaksi **tidak** memanggil AI.

## 6. AI Boundary
- AI hanya di **AI Adapter** di belakang antarmuka internal (`parseTransaction(text) → draft`).
- **Input ke provider:** teks transaksi + daftar kategori/akun yang relevan
  (seminimal mungkin). **Tidak** mengirim seluruh riwayat/PII yang tak perlu.
- **Output:** JSON terstruktur (type, amount, from/to account, category, date,
  note, confidence). Selalu divalidasi ulang; tebakan low-confidence ditandai.
- AI **tidak** menghitung saldo, **tidak** menulis DB, **tidak** memutuskan
  final — itu domain Financial Engine + konfirmasi pengguna.
- Provider spesifik = Open Question (lihat §11). Adapter membuatnya mudah diganti.

## 7. Financial Engine Boundary
- **Modul murni & deterministik** — tidak ada I/O jaringan, tidak ada AI.
- Sumber kebenaran aturan = `docs/FINANCIAL_RULES.md`.
- Tanggung jawab: menerapkan efek tiap tipe transaksi, mencegah double counting
  (CC), menghitung `balance / net_cash_flow / net_worth`, mendeteksi kandidat
  duplikat. Mudah diuji unit (lihat test cases FINANCIAL_RULES).

## 8. Security Boundary
- **Auth minimal** untuk MVP (single-user), setiap data ter-scope `user_id`.
- **HTTPS** untuk semua trafik klien–server.
- **Secrets** (API key LLM) hanya di server via env var; tidak pernah di klien.
- **Minimalkan data ke pihak ketiga** (AI provider) — hanya yang perlu untuk parse.
- Data keuangan bersifat pribadi; siapkan kemampuan hapus data (hak pengguna).
- Validasi input di server (jangan percaya klien).

## 9. Technology Recommendation (MVP)
> Rekomendasi, **belum final** — bergantung pada jawaban Open Questions produk.
> Dipilih untuk kesederhanaan solo-dev & iterasi cepat.

| Lapisan | Rekomendasi MVP | Alasan |
|---------|-----------------|--------|
| Frontend | **PWA** (satu SPA ringan, mis. React/Svelte) | Cepat iterasi, tanpa app store, mobile-first |
| Voice | **Web Speech API** (browser) | Gratis, cukup untuk validasi hipotesis; ganti nanti bila kurang akurat |
| Backend | **Modular monolith, TypeScript (Node)** *atau* **Python (FastAPI)** | Satu bahasa end-to-end (TS) atau ekosistem AI kuat (Py); pilih satu |
| Database | **SQLite** (file) untuk MVP → **PostgreSQL** saat tumbuh | Zero-ops untuk single-user; skema dirancang portabel |
| AI | LLM dengan **structured output (JSON)**, di balik adapter | Provider TBD; adapter = mudah ganti |
| Auth | Token sederhana / single-user | Sesuai MVP single-user (DECISIONS) |
| Money | **Integer minor unit (rupiah)** | Hindari error floating point |

## 10. Trade-offs
- **Monolith vs microservices:** monolith menang untuk MVP (lebih sederhana,
  cukup untuk skala single-user). Migrasi nanti bila benar-benar perlu.
- **SQLite vs Postgres:** SQLite = nol operasional tetapi lemah untuk konkurensi
  tinggi/multi-user. Skema dijaga portabel agar migrasi murah.
- **Browser STT vs STT berbayar:** browser gratis & cepat, tetapi akurasi/aksen
  bervariasi; fallback teks selalu tersedia. Tingkatkan hanya jika metrik buruk.
- **Saldo dihitung vs disimpan:** menghitung dari transaksi menjamin konsistensi
  (aman untuk edit/hapus) dengan biaya komputasi; boleh di-cache bila perlu.
- **AI di satu endpoint:** membatasi biaya & area kepercayaan, dengan konsekuensi
  alur dua langkah (parse lalu simpan) — sesuai prinsip "draft dulu".

## 11. OPEN ARCHITECTURE QUESTIONS
Belum diputuskan — disertai rekomendasi. Bergantung pada Open Questions produk.
1. **Bahasa backend: TypeScript/Node atau Python/FastAPI?**
   → _Rekomendasi:_ TypeScript bila ingin satu bahasa & berbagi tipe dengan
   frontend; Python bila ingin ekosistem AI lebih kaya. Default penulis: **TypeScript** untuk solo-dev fullstack.
2. **Framework frontend (React vs Svelte vs lainnya)?**
   → _Rekomendasi:_ pilih yang paling dikuasai; kompleksitas UI MVP rendah.
3. **Auth MVP: single local user tanpa login, atau token sederhana?**
   → _Rekomendasi:_ single-user tanpa login untuk MVP; siapkan `users` agar mudah ditambah auth.
4. **Provider LLM & STT** → mengacu ke Open Questions di PRODUCT_REQUIREMENTS.

---

_Dokumen ini menetapkan batas komponen. Skema data detail ada di
`docs/DATABASE_DESIGN.md`._
