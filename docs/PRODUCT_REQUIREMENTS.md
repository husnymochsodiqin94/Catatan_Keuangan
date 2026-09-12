# PRODUCT REQUIREMENTS — AI Financial Assistant

_Versi 1.0 · 2026-09-12 · Tahap 1: Product Discovery_
_Disusun dari perspektif Product Owner, Business Analyst, dan Financial Product Specialist._

> Prinsip pemandu: **catat transaksi secepat mungkin, tanpa form manual.**
> Alur inti: `Voice/Text → AI memahami → Transaksi terstruktur → Validasi → Financial Engine → Database`.

---

## 1. Problem Statement
Pencatatan keuangan pribadi gagal bukan karena orang tidak mau, tetapi karena
**friksinya terlalu tinggi**. Aplikasi keuangan umum menuntut pengguna membuka
app, memilih kategori dari daftar panjang, mengetik nominal, memilih akun, dan
menyimpan — 5–7 langkah untuk satu transaksi. Akibatnya pencatatan tertunda,
lupa, lalu ditinggalkan, dan data keuangan jadi tidak akurat.

**Core problem:** Bagaimana membuat pengguna dapat mencatat transaksi keuangan
**secepat mungkin** (idealnya satu kalimat) tanpa mengisi form manual?

## 2. Product Vision
Pengguna cukup **mengucapkan atau mengetik satu kalimat natural**, AI memahami
maksudnya, dan sistem mencatat transaksi terstruktur secara otomatis.
Pencatatan keuangan harus secepat mengirim satu pesan singkat.

## 3. Target User
- Individu dewasa (kira-kira 20–40 tahun) yang melek smartphone.
- Ingin tahu ke mana uangnya pergi, tetapi malas/ tidak konsisten mencatat manual.
- Transaksi harian bervolume kecil-menengah (jajan, transport, belanja, tagihan).
- Terbiasa berbicara ke asisten suara / mengetik chat.
- **Bukan** target awal: akuntan bisnis, pengelola keuangan perusahaan, investor aktif.

## 4. User Persona

**Persona A — "Dina, si Sibuk Praktis" (persona utama)**
- 27 tahun, karyawan kantoran, mobile-first.
- Nyeri: sering lupa uang habis ke mana; pernah pakai app keuangan tapi berhenti karena ribet.
- Motivasi: ingin catatan cepat tanpa mikir kategori.
- Sukses baginya: "cukup ngomong sekali, sudah tercatat."

**Persona B — "Rio, si Perencana" (persona sekunder)**
- 34 tahun, ingin budgeting rapi dan lihat laporan bulanan.
- Nyeri: input manual makan waktu; ingin akurasi kategori.
- Motivasi: kontrol & insight pengeluaran.
- Sukses baginya: data lengkap & bisa direview/dikoreksi.

## 5. Jobs To Be Done (JTBD)
- Ketika **baru saja bertransaksi**, saya ingin **mencatatnya dalam hitungan
  detik**, supaya **tidak lupa dan tidak terganggu aktivitas saya**.
- Ketika **AI salah menebak** kategori/akun/nominal, saya ingin
  **mengoreksinya dengan cepat**, supaya **data tetap akurat**.
- Ketika **ingin tahu kondisi keuangan**, saya ingin **melihat ringkasan
  pemasukan/pengeluaran**, supaya **bisa mengambil keputusan**.
- Ketika **mengucapkan sesuatu yang ambigu**, saya ingin **sistem bertanya
  singkat / menandai** daripada salah mencatat diam-diam.

## 6. Core User Journey
1. Pengguna membuka app / menekan tombol rekam (atau mengetik).
2. Mengucapkan/mengetik: _"Beli kopi 35 ribu pakai BCA."_
3. Sistem menampilkan hasil ekstraksi terstruktur (jenis, nominal, kategori, akun, tanggal).
4. Pengguna mengonfirmasi (1 tap) atau mengoreksi jika ada yang salah.
5. Transaksi tersimpan; saldo/ringkasan terbarui.
6. Pengguna kembali ke aktivitasnya. Total interaksi: beberapa detik.

## 7. User Flow (MVP)
```
[Input: Voice atau Text]
        │
        ▼
(jika voice) Speech-to-Text → teks
        │
        ▼
AI Ekstraksi Entitas
  → jenis, nominal, kategori, akun, tanggal, deskripsi
        │
        ▼
Validasi
  ├─ Lengkap & valid? ── ya ─► Tampilkan draft transaksi
  └─ Ada yang hilang/ambigu ─► Tandai field + minta konfirmasi/isi
        │
        ▼
Konfirmasi pengguna (konfirmasi / koreksi)
        │
        ▼
Financial Engine
  → normalisasi nominal, tentukan tanda (+/-), update saldo akun
        │
        ▼
Simpan ke Database
        │
        ▼
Umpan balik: "Tercatat" + ringkasan singkat
```

## 8. Functional Requirements
Prioritas: **P0** (wajib MVP), **P1** (penting, bisa menyusul), **P2** (nanti).

| ID | Requirement | Prioritas |
|----|-------------|-----------|
| FR-1 | Input transaksi via **teks** bahasa natural | P0 |
| FR-2 | Input transaksi via **suara** (STT → teks) | P0 |
| FR-3 | Ekstraksi entitas oleh AI: jenis, nominal, kategori, akun, tanggal, deskripsi | P0 |
| FR-4 | Parsing nominal informal ("35 ribu", "1.2jt", "seratus rb") → angka | P0 |
| FR-5 | Parsing tanggal relatif ("hari ini", "kemarin", "3 hari lalu") | P0 |
| FR-6 | Tampilkan draft transaksi terstruktur sebelum simpan | P0 |
| FR-7 | Pengguna dapat mengoreksi field apa pun sebelum menyimpan | P0 |
| FR-8 | Simpan transaksi ke penyimpanan | P0 |
| FR-9 | Lihat daftar/riwayat transaksi | P0 |
| FR-10 | Kelola daftar akun/sumber dana (mis. BCA, tunai, e-wallet) | P0 |
| FR-11 | Set kategori & subkategori (dengan default bawaan) | P0 |
| FR-12 | Tandai transaksi ambigu / minta konfirmasi bila data kurang | P1 |
| FR-13 | Edit & hapus transaksi setelah tersimpan | P1 |
| FR-14 | Ringkasan pemasukan vs pengeluaran per periode | P1 |
| FR-15 | Saldo per akun | P1 |
| FR-16 | Multi-transaksi dalam satu ucapan ("kopi 35rb dan parkir 5rb") | P2 |
| FR-17 | Kategori kustom oleh pengguna | P2 |

## 9. Non-Functional Requirements
- **Kecepatan:** dari selesai bicara → draft transaksi muncul idealnya < ~3 detik.
- **Akurasi ekstraksi:** target awal ≥ 85% field benar tanpa koreksi (lihat metrik).
- **Kemudahan koreksi:** memperbaiki satu field ≤ 2 tap.
- **Privasi & keamanan:** data keuangan bersifat pribadi; harus terlindungi
  saat transit & disimpan. (Detail mekanisme → Open Questions.)
- **Ketersediaan offline:** input tetap bisa dilakukan; pemrosesan AI mungkin
  butuh jaringan (perlu ditetapkan — Open Questions).
- **Lokalisasi:** Bahasa Indonesia sebagai bahasa utama input, termasuk gaya
  informal & campuran.
- **Biaya AI terkendali:** penggunaan model/STT harus efisien secara biaya.

## 10. MVP Scope
Tujuan MVP: **buktikan bahwa input natural lebih cepat & cukup akurat** untuk
mencatat transaksi harian, untuk **satu pengguna**.

**Termasuk:** FR-1 s/d FR-11 (input teks + suara, ekstraksi, draft+koreksi,
simpan, riwayat, akun, kategori default).
**Tidak termasuk di MVP:** laporan/analitik mendalam, budgeting, multi-user,
integrasi bank, multi-transaksi per ucapan, kategori kustom kompleks.

## 11. Phase 2
- Ringkasan & laporan periodik (FR-14, FR-15).
- Konfirmasi cerdas untuk transaksi ambigu (FR-12) yang lebih matang.
- Multi-transaksi dalam satu ucapan (FR-16).
- Kategori kustom (FR-17).
- Pencarian & filter riwayat.

## 12. Phase 3
- Budgeting & target pengeluaran per kategori.
- Insight/anjuran berbasis pola (mis. "pengeluaran kopi naik 30%").
- Transaksi berulang & pengingat tagihan.
- Ekspor data (CSV) & kemungkinan integrasi bank/e-wallet.
- (Opsional jauh) multi-perangkat / multi-user.

## 13. Product Success Metrics
- **Time-to-log:** median waktu dari mulai input → transaksi tersimpan (target < 10 detik).
- **Extraction accuracy:** % field benar tanpa koreksi (target ≥ 85% MVP).
- **Correction rate:** % transaksi yang butuh koreksi manual (semakin rendah semakin baik).
- **Logging consistency:** rata-rata transaksi tercatat per pengguna aktif per minggu.
- **Retention:** % pengguna yang masih mencatat setelah 1 & 4 minggu.
- **Voice vs Text share:** proporsi input suara vs teks (validasi hipotesis suara).
- **Abandonment:** % draft yang dibatalkan sebelum disimpan.

## 14. Risiko Produk
| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| Akurasi ekstraksi rendah → pengguna frustrasi | Tinggi | Draft + koreksi cepat; iterasi prompt; kumpulkan contoh koreksi |
| STT lemah untuk gaya bicara/aksen/campur bahasa | Tinggi | Sediakan fallback teks; pilih STT yang kuat untuk id-ID |
| Biaya AI/STT membengkak per transaksi | Menengah | Batasi panjang input; cache; pilih model efisien |
| Kesalahan diam-diam (silent wrong) merusak kepercayaan | Tinggi | Wajib tampilkan draft sebelum simpan; tandai low-confidence |
| Ambiguitas kategori (kopi = jajan? hadiah?) | Menengah | Default masuk akal + mudah dikoreksi; belajar dari koreksi (Phase 2+) |
| Kepekaan privasi data keuangan | Tinggi | Keamanan penyimpanan & transit; minimalkan data yang dikirim ke pihak ketiga |
| Over-engineering jadi app akunting kompleks | Menengah | Jaga MVP tetap sempit; patuhi prinsip di CLAUDE.md |

## 15. Edge Cases Utama
- Nominal ambigu/informal: "35rb", "35.000", "35k", "seratus ribu", "1,5 juta".
- Tanpa akun disebut → butuh default akun atau konfirmasi.
- Tanpa jenis eksplisit → tebak dari kata kerja ("beli"→pengeluaran, "terima/gajian"→pemasukan).
- Tanggal relatif/kompleks: "kemarin", "Senin lalu", "awal bulan".
- Multi-transaksi dalam satu kalimat (MVP: tangani 1, sisanya Phase 2).
- Input bukan transaksi (mis. "halo") → jangan buat transaksi; beri umpan balik.
- Mata uang non-IDR atau angka tanpa satuan.
- Koreksi setelah simpan (edit/hapus).
- STT salah dengar → pengguna bisa edit teks mentah.
- Angka ganda dalam kalimat ("beli 2 kopi 35 ribu") → nominal vs kuantitas.
- Nilai negatif/refund/pengembalian dana.
- Duplikat tidak sengaja (submit dua kali).

---

## OPEN PRODUCT QUESTIONS
Hal yang belum jelas — **belum diputuskan**, disertai rekomendasi. Mohon
keputusan Anda sebelum masuk arsitektur.

1. **Platform utama?** (mobile app / web / chat seperti WhatsApp-bot)
   → _Rekomendasi:_ mulai dari satu platform yang cepat untuk suara — **mobile-web / PWA** agar iterasi cepat tanpa kompleksitas store. Keputusan final Anda.
2. **Penyedia STT (Speech-to-Text)?**
   → _Rekomendasi:_ pakai STT bahasa Indonesia yang kuat; untuk MVP boleh andalkan STT bawaan browser/OS dulu agar hemat biaya, evaluasi akurasi, baru tingkatkan.
3. **Penyedia model AI untuk ekstraksi?**
   → _Rekomendasi:_ gunakan LLM dengan output terstruktur (JSON) + prompt berbahasa Indonesia. Pemilihan vendor spesifik ditunda ke tahap arsitektur.
4. **Selalu online atau perlu offline?**
   → _Rekomendasi:_ MVP online-first (ekstraksi butuh jaringan), input teks bisa disimpan lokal saat offline lalu diproses saat online.
5. **Wajib konfirmasi draft atau auto-save?**
   → _Rekomendasi:_ **wajib tampilkan draft** di MVP demi kepercayaan; auto-save untuk kasus high-confidence bisa Phase 2.
6. **Multi-user / login sekarang?**
   → _Rekomendasi:_ MVP **single-user**, tanpa auth kompleks; siapkan model data agar mudah ditambah user nanti.
7. **Set kategori & akun default?**
   → _Rekomendasi:_ sediakan seperangkat kategori umum Indonesia (Makanan & Minuman, Transport, Belanja, Tagihan, dll.) + akun umum (Tunai, BCA, e-wallet); bisa diedit.
8. **Bagaimana menangani low-confidence extraction?**
   → _Rekomendasi:_ tandai field ber-confidence rendah dan minta konfirmasi, jangan diam-diam menyimpan tebakan.
9. **Retensi & kepemilikan data?**
   → _Rekomendasi:_ tetapkan sejak awal bahwa data milik pengguna, dapat dihapus; minimalkan data yang dikirim ke layanan pihak ketiga.

---

_Dokumen ini mendefinisikan **apa** dan **mengapa**. Keputusan **bagaimana**
(stack, arsitektur, skema data) menyusul pada tahap berikutnya, setelah Open
Questions terjawab._
