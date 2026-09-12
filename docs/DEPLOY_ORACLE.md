# Deploy GRATIS: Oracle Cloud "Always Free" + DuckDNS

Panduan langkah demi langkah menjalankan aplikasi ini **gratis selamanya** dengan
**data tersimpan permanen**. Perkiraan waktu pertama kali: ~45–60 menit.

Butuh: email, dan **kartu (hanya untuk verifikasi identitas — tidak ditagih** selama
memakai sumber daya "Always Free"). Aplikasi kita ringan; VM Always Free lebih dari cukup.

---

## 1. Buat akun Oracle Cloud
1. Buka https://www.oracle.com/cloud/free/ → **Start for free**.
2. Isi data, pilih negara **Indonesia**, verifikasi email & nomor HP.
3. Masukkan kartu untuk verifikasi (tertera "won't be charged" untuk Always Free).
4. Pilih **Home Region** terdekat (mis. *Singapore* / *Jakarta* bila tersedia).
   Catatan: region tidak bisa diganti setelah dipilih.

## 2. Buat VM "Always Free"
1. Menu ☰ → **Compute → Instances → Create instance**.
2. **Image & shape:**
   - Image: **Canonical Ubuntu 22.04** (atau 24.04).
   - Shape: klik **Change shape** → pilih yang berlabel **Always Free-eligible**:
     - **Ampere (VM.Standard.A1.Flex)** — ARM, mis. 1 OCPU / 6 GB (paling lega), atau
     - **VM.Standard.E2.1.Micro** — AMD kecil (juga Always Free).
   - (Dockerfile kita jalan di ARM maupun AMD — keduanya oke.)
3. **SSH keys:** pilih **Generate a key pair for me** → **unduh private key** (simpan
   baik-baik, mis. `oracle_key`). Ini untuk login SSH.
4. Biarkan sisanya default → **Create**. Tunggu status **Running**.
5. Catat **Public IP address** instance (mis. `152.x.x.x`).

> Jika muncul "Out of capacity" saat memilih Ampere, coba lagi beberapa saat, atau
> pakai shape **E2.1.Micro**, atau region lain.

## 3. Buka port 80 & 443 (Security List)
1. Dari halaman instance → klik nama **Virtual Cloud Network (VCN)**-nya.
2. **Security Lists** → **Default Security List** → **Add Ingress Rules**, buat dua:
   - Source `0.0.0.0/0`, IP Protocol **TCP**, Destination Port **80**.
   - Source `0.0.0.0/0`, IP Protocol **TCP**, Destination Port **443**.
   (Port 22/SSH biasanya sudah terbuka.)

## 4. Domain gratis (DuckDNS)
1. Buka https://www.duckdns.org → **sign in** (Google/GitHub).
2. Ketik subdomain yang diinginkan (mis. `catatanku`) → **add domain** →
   jadi `catatanku.duckdns.org`.
3. Pada baris subdomain, isi kolom **current ip** dengan **Public IP VM** (langkah 2.5)
   → klik **update ip**.

## 5. Login SSH ke VM
Dari komputer Anda (Linux/macOS/WSL/PowerShell):
```bash
chmod 600 oracle_key          # (Linux/macOS)
ssh -i oracle_key ubuntu@PUBLIC_IP_VM
```
(User default image Ubuntu Oracle = `ubuntu`.)

## 6. Jalankan aplikasi (satu jalan)
Di dalam VM:
```bash
sudo apt-get update -y && sudo apt-get install -y git
git clone <URL-REPO-ANDA> && cd Catatan_Keuangan
sudo bash deploy/setup.sh catatanku.duckdns.org
```
Skrip akan: memasang Docker, membuat `.env` (DOMAIN + token acak otomatis — **catat
tokennya**), membuka firewall OS, lalu `docker compose up -d --build`.

Selesai → buka **https://catatanku.duckdns.org**. Caddy otomatis menerbitkan HTTPS
(butuh beberapa detik pada akses pertama). Saat aplikasi minta token, tempel
`CATATAN_TOKEN` yang dicetak skrip.

## 7. Operasional
- **Lihat log:** `docker compose logs -f`
- **Update aplikasi:** `git pull && docker compose up -d --build`
- **Backup data:** salin volume `catatan-data` (SQLite). Cepatnya:
  `docker run --rm -v catatan_keuangan_catatan-data:/d -v $PWD:/b alpine tar czf /b/backup.tgz -C /d .`
- **Email alert (opsional):** edit `.env` isi `SMTP_*`, lalu `docker compose up -d`.
- **Kirim alert terjadwal (opsional):** tambah cron di VM:
  `0 20 * * * curl -s -X POST -H "X-Token: <TOKEN>" https://catatanku.duckdns.org/api/alerts/send`

## Masalah umum
- **Situs tidak terbuka / HTTPS gagal:** pastikan (a) Security List Oracle membuka 80/443,
  (b) DuckDNS mengarah ke IP VM yang benar, (c) `docker compose logs caddy` untuk pesan sertifikat.
- **"Out of capacity" Ampere:** ulangi, ganti shape E2.1.Micro, atau region lain.
- **IP VM berubah** (bila instance sempat di-stop/start dengan IP ephemeral): perbarui IP di
  DuckDNS. Untuk stabil, di Oracle bisa jadikan Public IP **Reserved**.
