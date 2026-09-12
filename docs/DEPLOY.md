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

> **Mau gratis?** Panduan lengkap gratis (Oracle Cloud Always Free + DuckDNS),
> klik-demi-klik: **`docs/DEPLOY_ORACLE.md`**. Jalur di bawah ini generik untuk
> server/domain apa pun.

## Deploy A — Docker + Caddy (HTTPS otomatis) — disarankan
Butuh: server dengan Docker + domain yang mengarah ke IP server (A record).

```bash
git clone <repo> && cd Catatan_Keuangan
cp .env.example .env
# edit .env: isi DOMAIN (mis. keuangan.contoh.com) & CATATAN_TOKEN
#   token acak:  python3 -c "import secrets;print(secrets.token_urlsafe(32))"
docker compose up -d --build
```
- Caddy otomatis menerbitkan sertifikat HTTPS (Let's Encrypt) untuk `DOMAIN`.
- App di-`expose` internal (port 8000), hanya Caddy yang membuka 80/443.
- Data tersimpan di volume `catatan-data` (SQLite `/data/data.db`).
- Cek: `docker compose logs -f`, health: `https://DOMAIN/api/health`.
- Update: `git pull && docker compose up -d --build`.
- Uji lokal tanpa domain: biarkan `DOMAIN=localhost` → Caddy pakai sertifikat
  self-signed (browser akan memperingatkan; wajar untuk uji).

File terkait: `Dockerfile`, `docker-compose.yml`, `deploy/Caddyfile`, `.env`.

## Deploy B — VPS tanpa Docker (systemd + reverse proxy)
```bash
sudo useradd -r -s /usr/sbin/nologin catatan
sudo mkdir -p /opt/catatan && sudo cp -r . /opt/catatan && sudo chown -R catatan /opt/catatan
sudo cp deploy/catatan.service /etc/systemd/system/
# edit unit: set CATATAN_TOKEN (dan SMTP_* bila pakai email)
sudo systemctl daemon-reload && sudo systemctl enable --now catatan
```
Lalu pasang **Caddy/Nginx** di depan dengan HTTPS, reverse-proxy ke
`127.0.0.1:8000`. Contoh Caddyfile satu baris: `keuangan.contoh.com { reverse_proxy 127.0.0.1:8000 }`.

## Setelah online
- **Auth:** karena `CATATAN_TOKEN` diset, saat pertama kali API menolak (401)
  aplikasi meminta token; token disimpan di browser.
- **Email otomatis:** jadwalkan `POST /api/alerts/send` (dengan header `X-Token`)
  via cron, mis. harian:
  `0 20 * * *  curl -s -X POST -H "X-Token: $TOKEN" https://DOMAIN/api/alerts/send`
- **Backup:** salin volume/`data.db` secara berkala.
- **HTTPS wajib**: mikrofon (Web Speech) & pemasangan PWA hanya aktif di HTTPS.

## Catatan
- MVP single-user; token bersifat bersama (bukan multi-akun). Multi-user + login
  proper adalah pekerjaan berikutnya bila diperlukan.
- Semua perhitungan finansial dilakukan Financial Engine; server & frontend tidak
  menghitung ulang.
