# Panduan Rilis ke Google Play Store (Android)

Aplikasi ini adalah **PWA** (Progressive Web App). Cara termudah masuk Play
Store adalah membungkusnya sebagai **TWA (Trusted Web Activity)** — Android
membuka PWA-mu dalam wadah aplikasi native, tanpa menulis ulang kodenya.

> Ringkas: **Deploy online (HTTPS) → bungkus jadi TWA → unggah ke Play Console.**

---

## 0. Prasyarat (WAJIB sebelum mulai)

| # | Prasyarat | Catatan |
|---|-----------|---------|
| 1 | **Aplikasi online di domain HTTPS** | TWA memuat URL publik. Lihat `docs/DEPLOY.md` / `docs/DEPLOY_ORACLE.md`. Subdomain gratis (mis. `namamu.duckdns.org`) bisa dipakai. |
| 2 | **PWA installable** | Sudah terpenuhi: manifest + service worker + ikon 192/512 + maskable. |
| 3 | **Akun Google Play Console** | Sekali bayar **$25** seumur hidup: https://play.google.com/console |
| 4 | **Kebijakan Privasi (URL publik)** | Play mewajibkan halaman privasi. Buat satu halaman sederhana (boleh di domain yang sama, mis. `/privacy`). |
| 5 | **JDK 17 + Android SDK** | Hanya untuk jalur Bubblewrap (opsi B). Opsi A (PWABuilder) tidak perlu. |

---

## 1. Cek kesiapan PWA

1. Buka aplikasi online-mu di Chrome Android → menu ⋮ → **Add to Home screen**.
   Jika muncul dan terpasang seperti aplikasi (tanpa address bar), PWA siap.
2. Uji dengan **Lighthouse** (Chrome DevTools → tab Lighthouse → kategori PWA).
   Pastikan "Installable" hijau.

---

## 2. Bungkus jadi aplikasi Android (pilih SATU jalur)

### Opsi A — PWABuilder (paling mudah, berbasis web) ✅ disarankan

1. Buka **https://www.pwabuilder.com**
2. Masukkan URL aplikasimu (mis. `https://namamu.duckdns.org`) → **Start**.
3. PWABuilder menilai manifest & service worker. Perbaiki peringatan bila ada.
4. Klik **Package For Stores → Android → Generate Package**.
   - **Package ID**: mis. `com.namamu.keuangan` (huruf kecil, unik, tak bisa diubah setelah rilis).
   - Centang **Signing key: buat baru** → PWABuilder membuat keystore.
     **SIMPAN file keystore + password baik-baik** (hilang = tak bisa update aplikasi selamanya).
5. Unduh ZIP. Isinya:
   - `app-release-signed.aab` — file untuk diunggah ke Play.
   - `assetlinks.json` — **file verifikasi** (lihat langkah 3).
   - `signing key` + petunjuk.

### Opsi B — Bubblewrap (CLI, lebih teknis)

```bash
npm i -g @bubblewrap/cli
bubblewrap init --manifest https://namamu.duckdns.org/manifest.webmanifest
# jawab: package id, nama, warna, dll.
bubblewrap build            # menghasilkan app-release-signed.aab + assetlinks
```
Bubblewrap membuat keystore di `android.keystore` — **backup file ini + passwordnya**.

---

## 3. Digital Asset Links (menghapus address bar)

Agar TWA tampil **fullscreen tanpa bar URL**, domainmu harus "mengakui" aplikasi:

1. Ambil `assetlinks.json` dari hasil langkah 2.
2. Taruh agar bisa diakses di:
   `https://namamu.duckdns.org/.well-known/assetlinks.json`
   - Buat folder `webapp/.well-known/` dan letakkan file di sana, atau atur
     server/Caddy untuk menyajikannya. (Isi file = SHA-256 sidik jari keystore-mu.)
3. Verifikasi: buka URL di atas di browser → harus muncul JSON, bukan 404.

> Tanpa ini aplikasi tetap jalan, tapi ada bilah alamat kecil di atas.

---

## 4. Unggah ke Play Console

1. Masuk **https://play.google.com/console** → **Create app**.
   - Nama, bahasa default (Indonesia), tipe **App**, **Free**.
2. Lengkapi **Store listing**:
   - Deskripsi singkat & panjang.
   - **Ikon 512×512** → pakai `webapp/icon-512.png`.
   - **Feature graphic 1024×500** (banner) — perlu dibuat terpisah.
   - **Minimal 2 screenshot HP** — ambil dari aplikasi berjalan.
3. Isi kuesioner wajib: **Kebijakan Privasi (URL)**, **Data safety**,
   **Content rating**, **Target audience**, **Ads (tidak ada)**.
4. **Production → Create release** → unggah `app-release-signed.aab`.
5. **Review**: kirim. Peninjauan Google biasanya beberapa jam s/d beberapa hari.

---

## 5. Update aplikasi ke depan

- **Konten web (fitur/tampilan):** cukup deploy ulang ke server. TWA memuat
  web terbaru **otomatis** — pengguna tak perlu update dari Play. 🎉
- **Hal native (ikon, nama, target SDK):** naikkan `versionCode`, build ulang
  dengan **keystore yang sama**, unggah `.aab` baru ke Play.

---

## Alternatif tanpa Play Store (tercepat, gratis)

Setelah aplikasi online, pengguna bisa **"Add to Home screen"** dari Chrome —
langsung terpasang seperti aplikasi (ikon, fullscreen, offline), **tanpa**
Play Store, tanpa biaya, tanpa review. Cocok untuk pemakaian pribadi/keluarga
atau uji coba sebelum benar-benar rilis ke Play.

---

## Checklist singkat

- [ ] Aplikasi online di HTTPS (domain/subdomain).
- [ ] Halaman Kebijakan Privasi publik.
- [ ] Lighthouse PWA "Installable" hijau.
- [ ] Paket TWA (`.aab`) + keystore dibuat & **di-backup**.
- [ ] `assetlinks.json` tersaji di `/.well-known/`.
- [ ] Akun Play Console ($25) aktif.
- [ ] Store listing (ikon 512, feature graphic, screenshot) lengkap.
- [ ] Rilis Production diunggah & dikirim untuk review.
