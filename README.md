# AI Financial Assistant (nama sementara)

Aplikasi pencatatan keuangan pribadi berbasis bahasa natural — terutama suara.
Ucapkan satu kalimat, AI memahami, sistem mencatat transaksinya otomatis.

> Contoh: _"Beli kopi 35 ribu pakai BCA"_ → pengeluaran Rp35.000, kategori
> Makanan & Minuman → Kopi, akun BCA, tanggal hari ini.

## Status
MVP berjalan sebagai **PWA + backend Python** (tanpa dependency pihak ketiga). Lihat `docs/PROJECT_STATUS.md`.

## Menjalankan (butuh Python 3.11+, tanpa install apa pun)
```bash
python3 -m server.app          # buka http://127.0.0.1:8000
python3 -m unittest discover -s tests -t .   # jalankan test (78 test)
```
Deploy & konfigurasi (auth token, email SMTP): `docs/DEPLOY.md`.
Deploy GRATIS langkah-demi-langkah (Oracle Cloud + DuckDNS): `docs/DEPLOY_ORACLE.md`.
- Backend: `server/` — HTTP stdlib + SQLite, membungkus `financial_engine`/`nlp`/`reporting`.
- Frontend PWA: `webapp/` — disajikan oleh backend di origin yang sama.
- Data tersimpan di `data.db` (SQLite, tidak di-commit).

## Struktur
- `financial_engine/` — inti logika keuangan (deterministik, teruji).
- `nlp/` — parser bahasa natural → transaksi (rule-based; adapter LLM menyusul).
- `voice/` — voice → STT → pipeline (adapter; STT nyata menyusul).
- `reporting/` — penyusun data dashboard dari engine.
- `server/` — API JSON + penyajian PWA.
- `webapp/` — PWA (HTML/CSS/JS, tanpa build step).

## Dokumentasi
- `CLAUDE.md` — aturan utama & alur kerja pengembangan.
- `docs/PRODUCT_VISION.md` — visi & lingkup produk.
- `docs/PROJECT_STATUS.md` — status terkini.
- `docs/DECISIONS.md` — catatan keputusan arsitektur.
