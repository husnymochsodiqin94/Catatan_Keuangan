# Deploy Gratis di Google Cloud (Always Free VM) + DuckDNS

Menjalankan aplikasi online (HTTPS) di VM **e2-micro "Always Free"** Google
Cloud. Data (`data.db`) tersimpan permanen di disk VM. Semua lewat **browser** —
tidak perlu aplikasi SSH tambahan.

> Alur: buat VM → domain gratis DuckDNS → SSH lewat browser → 1 skrip jalan.

---

## 0. Yang dibutuhkan
- Akun Google + **kartu debit/kredit** (untuk verifikasi; tetap gratis).
- Repo ini (branch `claude/financial-assistant-setup-n1aqkd`).

---

## 1. Daftar Google Cloud
1. Buka **https://console.cloud.google.com** → login → **Aktifkan free trial**
   (dapat kredit $300, tapi VM e2-micro tetap gratis selamanya di luar kredit).
2. Isi data + verifikasi kartu.

---

## 2. Buat VM e2-micro (WAJIB region Always Free)

1. Menu ☰ → **Compute Engine → VM instances** → **Create instance**.
2. Isi:
   - **Name**: `keuangan`
   - **Region**: pilih **SALAH SATU** yang gratis: `us-west1` (Oregon),
     `us-central1` (Iowa), atau `us-east1` (South Carolina). ⚠️ Region lain **berbayar**.
   - **Machine type**: seri **E2** → **`e2-micro`** (0.25–2 vCPU, 1 GB). ⚠️ Harus e2-micro.
   - **Boot disk**: **Ubuntu 22.04 LTS**, tipe **Standard persistent disk**,
     ukuran **30 GB** (batas gratis).
   - **Firewall**: centang **Allow HTTP traffic** dan **Allow HTTPS traffic**.
3. **Create**. Tunggu VM hijau, catat **External IP** (mis. `34.83.x.x`).

> Tips: agar IP tidak berubah, VPC network → IP addresses → **Reserve** IP eksternal
> lalu attach ke VM (gratis selama menempel di VM aktif). Opsional.

---

## 3. Domain gratis DuckDNS → arahkan ke IP VM
1. Buka **https://www.duckdns.org** → login (Google).
2. Buat subdomain, mis. `keuanganku` → jadi `keuanganku.duckdns.org`.
3. Di kolom **current ip**, isi **External IP VM** (langkah 2) → **update ip**.

---

## 4. Masuk VM lewat browser (SSH)
1. Di daftar VM, klik tombol **SSH** di baris VM → jendela terminal terbuka di browser.
   (Tidak perlu PuTTY / kunci SSH.)

---

## 5. Ambil kode & jalankan (di terminal SSH)

```bash
# 1) alat dasar
sudo apt-get update && sudo apt-get install -y git

# 2) ambil kode (branch pengembangan)
git clone -b claude/financial-assistant-setup-n1aqkd \
  https://github.com/husnymochsodiqin94/Catatan_Keuangan.git
cd Catatan_Keuangan

# 3) satu skrip: pasang Docker, buat .env, buka firewall OS, build & jalan
sudo bash deploy/setup.sh keuanganku.duckdns.org
```

Ganti `keuanganku.duckdns.org` dengan domainmu. Skrip akan:
- memasang Docker,
- membuat `.env` (mengisi DOMAIN),
- menjalankan aplikasi + Caddy (**HTTPS otomatis** dari Let's Encrypt).

Tunggu ±1–2 menit (build image). Selesai bila muncul `https://keuanganku.duckdns.org`.

---

## 6. Buka aplikasimu
Di HP/laptop, buka: **https://keuanganku.duckdns.org**
- Sertifikat HTTPS terbit otomatis (butuh domain sudah mengarah ke IP — langkah 3).
- **Daftar** akun baru, mulai mencatat. Data tersimpan di VM (permanen).

Dari sini kamu bisa lanjut **"Add to Home screen"** di HP (jadi seperti aplikasi),
atau bungkus jadi APK Play Store — lihat `docs/PUBLISH_PLAYSTORE.md`.

---

## Perawatan

| Kebutuhan | Perintah (di SSH, dalam folder `Catatan_Keuangan`) |
|-----------|----------------------------------------------------|
| Update kode terbaru | `git pull && docker compose up -d --build` |
| Lihat status | `docker compose ps` |
| Lihat log | `docker compose logs -f app` |
| Restart | `docker compose restart` |
| Backup data | `docker compose cp app:/data/data.db backup-$(date +%F).db` |

---

## Masalah umum
- **Situs tak bisa dibuka / HTTPS gagal:** pastikan (a) DuckDNS sudah mengarah ke
  IP VM, (b) VM mencentang Allow HTTP/HTTPS (atau buat firewall rule tcp:80,443).
  Cek log Caddy: `docker compose logs caddy`.
- **"e2-micro tetap kena biaya":** pastikan region `us-west1/us-central1/us-east1`
  dan hanya **1** VM e2-micro dengan disk ≤30 GB.
- **Lupa IP VM:** Compute Engine → VM instances → kolom External IP.
