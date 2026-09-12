# DEPLOY & KONFIGURASI

Aplikasi = backend Python stdlib (menyajikan API + PWA) + SQLite. Tanpa dependency
pihak ketiga. Berikut cara menjalankan lokal dan men-deploy.

## Jalankan lokal
```bash
python3 -m server.app          # http://127.0.0.1:8000
python3 -m unittest discover -s tests -t .   # 78 test
```
Data tersimpan di `data.db` (SQLite, tidak di-commit). Ganti lokasi via `CATATAN_DB`.

## Variabel lingkungan
| Env | Fungsi | Default |
|-----|--------|---------|
| `HOST` | alamat bind | `127.0.0.1` |
| `PORT` | port | `8000` |
| `CATATAN_DB` | path file SQLite | `data.db` |
| `CATATAN_TOKEN` | **bila diset**, semua `/api/*` (kecuali `/api/health`) butuh token (header `X-Token` atau `?token=`). Aktifkan saat online. | (kosong = tanpa auth, untuk lokal) |
| `SMTP_HOST` | host SMTP untuk alert email | — |
| `SMTP_PORT` | port SMTP | `587` |
| `SMTP_USER` / `SMTP_PASS` | kredensial SMTP (opsional) | — |
| `SMTP_FROM` | alamat pengirim | — |
| `SMTP_SSL` | `1` untuk SMTPS (SSL langsung), selain itu STARTTLS | (STARTTLS) |

Alert email hanya terkirim bila `SMTP_HOST` **dan** `SMTP_FROM` diset **dan** email
tujuan diisi di Pengaturan. Tanpa itu, alert tetap tampil in-app (banner) — endpoint
`POST /api/alerts/send` mengembalikan alasannya.

## Deploy (garis besar)
Karena hanya butuh Python, deploy sederhana:
1. **VPS / container:** jalankan `HOST=0.0.0.0 PORT=8000 CATATAN_TOKEN=<rahasia> python3 -m server.app` di belakang reverse proxy (Nginx/Caddy) dengan **HTTPS** (wajib agar Web Speech/mic & PWA install aktif).
2. **Auth:** set `CATATAN_TOKEN`. Klien memasukkan token sekali (disimpan di browser) — pertama kali API menolak (401), aplikasi meminta token.
3. **Email:** set variabel `SMTP_*` (mis. Amazon SES/SendGrid/Resend SMTP).
4. **Backup:** cukup salin file `data.db`.

Untuk mengirim alert email otomatis saat mendekati batas, panggil
`POST /api/alerts/send` secara terjadwal (mis. cron harian) atau tambahkan pemicu
saat transaksi disimpan (menyusul).

## Catatan
- MVP single-user; token bersifat bersama (bukan multi-akun). Multi-user + login
  proper adalah pekerjaan berikutnya bila diperlukan.
- Semua perhitungan finansial dilakukan Financial Engine; server & frontend tidak
  menghitung ulang.
