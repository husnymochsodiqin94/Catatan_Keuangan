# UX/UI MVP — AI Financial Assistant

_Versi 1.0 · 2026-09-12 · Tahap 4: UX/UI Design_
_Perspektif Senior Product Designer. Fokus pada UX terpenting: **mencatat
transaksi secepat mungkin**. Bukan membangun semua halaman._

> North Star UX: dari niat mencatat → transaksi tersimpan dalam **hitungan detik**,
> tanpa form panjang. Alur: `🎤/⌨️ Capture → AI paham → Preview → Simpan`.

---

## 1. Prinsip Desain
1. **Capture-first.** Layar utama = alat input. Tombol rekam/ketik selalu terlihat.
2. **Satu kalimat, satu transaksi.** Kurangi keputusan pengguna seminimal mungkin.
3. **Draft, bukan form.** AI mengisi; pengguna hanya mengonfirmasi/mengoreksi (sesuai DECISIONS).
4. **Koreksi ≤ 2 tap.** Setiap field draft bisa disentuh & diubah cepat.
5. **Kepercayaan lewat transparansi.** Tampilkan hasil AI + tanda low-confidence, jangan simpan diam-diam.
6. **Mobile-first / PWA** (dari SYSTEM_ARCHITECTURE).

---

## 2. Information Architecture

```
App (single user)
│
├── Home / Dashboard            ← titik masuk utama (Capture ada di sini)
│     ├── Ringkasan (net worth, cash flow bulan ini, saldo akun)
│     ├── ⬤ CAPTURE BAR (mic + teks)  ← elemen paling penting
│     └── Transaksi terbaru (shortcut ke History)
│
├── Capture (overlay/sheet)     ← muncul dari Dashboard
│     └── Confirmation (draft transaksi)  ← state lanjutan dari Capture
│
├── History                     ← daftar transaksi + filter
│     └── Transaction Detail / Edit
│
└── Settings
      ├── Accounts (kelola akun)
      └── Categories (kelola kategori)
```

**Navigasi utama (bottom nav, 3 tab):** `Home` · `History` · `Settings`.
Capture bukan tab — ia **aksi utama** yang menonjol di Home (dan FAB di layar lain).

---

## 3. Screen Hierarchy (prioritas)
| Prioritas | Layar | Alasan |
|-----------|-------|--------|
| P0 | **Capture (Voice/Text)** | Inti produk; harus tercepat |
| P0 | **Transaction Confirmation** | Titik kepercayaan; draft → simpan |
| P0 | **Dashboard** | Rumah + tempat capture berada |
| P1 | **Transaction History** | Melihat & mencari catatan |
| P1 | **Transaction Detail/Edit** | Koreksi setelah simpan |
| P1 | **Account Management** | Kebutuhan dasar akun (BCA, tunai, dll.) |
| P2 | **Category Management** | Default cukup untuk MVP awal |
| P2 | **Settings** | Wadah pengaturan & entry ke Accounts/Categories |

---

## 4. Core User Flow (happy path)
```
[Dashboard]
   │ tap mic / mulai ketik
   ▼
[Capture]  🎤 "Beli kopi 35 ribu pakai BCA"
   │ (loading: "Memahami…")
   ▼
[Confirmation]  draft:
   Pengeluaran · Rp35.000 · Makanan & Minuman ▸ Kopi · BCA · Hari ini
   [Simpan]   [Ubah field apa pun]
   │ tap Simpan
   ▼
[Saved toast]  "Tercatat ✓"  → kembali ke Dashboard (saldo & list terbarui)
```
**Total interaksi target:** 1 aksi bicara + 1 tap Simpan.

### Flow cabang penting
- **Field kurang/ambigu** → field ditandai, minta lengkapi sebelum Simpan.
- **Bukan transaksi** ("halo") → beri umpan balik, jangan buat transaksi.
- **Kandidat duplikat** → tampilkan peringatan "mirip transaksi X, tetap simpan?".
- **Koreksi** → tap field → picker/inline edit → kembali ke draft.

---

## 5. Spesifikasi Layar (ringkas)

### 5.1 Dashboard (P0)
- **Header ringkas:** Net worth + Cash flow bulan ini (in/out).
- **Capture bar menonjol:** tombol mic besar + field teks ("Ketik atau tekan mic…").
- **Saldo per akun** (chip/row).
- **Transaksi terbaru** (3–5 item) → link ke History.
- **Empty state:** ilustrasi + "Catat transaksi pertamamu — cukup ucapkan
  'Beli kopi 35 ribu'." + tombol mic.

### 5.2 Capture (P0)
- Mode **suara** (default) & **teks** (toggle/atau ketik langsung).
- Saat merekam: indikator dengar + transkrip live (jika ada).
- Bisa dibatalkan; bisa edit transkrip mentah sebelum diproses.

### 5.3 Transaction Confirmation (P0)
- **Kartu draft** dengan field terbaca: Jenis · Nominal · Kategori▸Sub · Akun · Tanggal · Catatan.
- Tiap field **tappable** untuk koreksi cepat (chip/stepper/picker, bukan form kosong).
- Field low-confidence diberi tanda (mis. garis putus/ikon "?").
- Aksi utama: **Simpan** (paling menonjol). Aksi sekunder: Batal.

### 5.4 Transaction History (P1)
- List dikelompokkan per tanggal; tiap item: ikon kategori, nama, akun, nominal (warna in/out).
- Filter: periode, tipe, akun. Search (Phase 2 boleh menyusul).
- **Empty state:** "Belum ada transaksi."

### 5.5 Transaction Detail / Edit (P1)
- Detail lengkap + tombol Edit & Hapus (soft delete).
- Edit memakai komponen sama seperti Confirmation.

### 5.6 Account Management (P1)
- List akun (nama, tipe, saldo). Tambah/edit/arsipkan (bukan hapus keras).
- Tipe: Cash / Bank / E-wallet / Credit Card.

### 5.7 Category Management (P2)
- Kategori + subkategori (default sistem + kustom nanti). Arsipkan, bukan hapus keras.

### 5.8 Settings (P2)
- Entry ke Accounts & Categories, preferensi dasar (akun default), hapus data.

---

## 6. Component Structure (reusable)
- `CaptureBar` — mic button + text input (dipakai di Dashboard & sebagai FAB).
- `DraftCard` — kartu transaksi editable (dipakai di Confirmation & Edit).
- `FieldChip` — satu field tappable (jenis/nominal/kategori/akun/tanggal).
- `TransactionRow` — baris item (History & Dashboard recent).
- `AmountText` — format Rupiah + warna in/out.
- `AccountRow` / `CategoryRow` — item manajemen.
- `SummaryHeader` — net worth & cash flow.
- `StateView` — pembungkus empty/loading/error/confirmation.
- `Toast` — umpan balik "Tercatat ✓".

---

## 7. UI States (untuk setiap layar interaktif)

| State | Perilaku |
|-------|----------|
| **Empty** | Ajakan aksi jelas + contoh kalimat + tombol mic (Dashboard/History/Accounts). |
| **Loading** | Capture→"Memahami…"; list→skeleton; hemat, tidak menutup seluruh layar bila bisa. |
| **Error** | Gagal STT/AI/jaringan → pesan ramah + **retry** + selalu ada **fallback ketik teks**. |
| **Confirmation** | Draft tampil sebelum simpan; low-confidence ditandai; Simpan menonjol. |
| **Success** | Toast "Tercatat ✓", Dashboard terbarui (saldo & recent). |
| **Ambiguous/Incomplete** | Field kurang ditandai; Simpan nonaktif sampai lengkap. |
| **Duplicate warning** | Banner "Mirip transaksi sebelumnya" + pilihan tetap simpan / batal. |

### Contoh microcopy (id-ID)
- Placeholder capture: _"Ketik atau tekan mic — mis. 'Beli kopi 35 ribu pakai BCA'"_
- Loading: _"Memahami…"_
- Error AI: _"Belum berhasil memahami. Coba ucapkan lagi atau ketik manual."_
- Bukan transaksi: _"Sepertinya ini bukan transaksi. Coba sebutkan nominalnya."_
- Sukses: _"Tercatat ✓"_

---

## 8. Prototype
Prototipe HTML statis (tanpa backend, parser tiruan) mendemonstrasikan alur inti
**Capture → Preview → Simpan**:
- Berkas: `docs/prototype/index.html` (buka di browser).
- Cakupan: Dashboard + Capture + Confirmation + Saved toast + recent list.
- Catatan: parsing di prototipe hanyalah tiruan (regex sederhana) untuk demo UX,
  **bukan** AI/financial engine sungguhan.

---

## 9. Di Luar Lingkup Tahap Ini
- Tidak membangun semua 8 halaman secara lengkap; fokus P0 (capture flow).
- Tidak ada backend, STT nyata, atau integrasi AI.
- Sistem visual final (branding, warna, tipografi) menyusul; prototipe memakai gaya netral.

## 10. OPEN UX QUESTIONS
1. **Suara vs teks sebagai default di Dashboard?**
   → _Rekomendasi:_ tombol mic menonjol, field teks tetap ada sejajar (fallback instan).
2. **Auto-save untuk hasil high-confidence?**
   → _Rekomendasi:_ tetap tampilkan draft di MVP (kepercayaan); auto-save Phase 2.
3. **Perlu onboarding singkat?**
   → _Rekomendasi:_ cukup empty state yang mengajari lewat contoh; skip onboarding formal.

---

_Dokumen ini mendefinisikan UX MVP & prioritas layar. Implementasi UI nyata
menunggu keputusan stack frontend (Open Questions arsitektur)._
