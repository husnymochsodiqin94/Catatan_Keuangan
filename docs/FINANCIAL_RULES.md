# FINANCIAL RULES — AI Financial Assistant

_Versi 1.0 · 2026-09-12 · Tahap 2: Financial Business Rules_
_Disusun dari perspektif Financial System Architect. Dokumen ini mendefinisikan
**logika keuangan**, bukan implementasi. Tanpa kode, UI, voice, atau AI._

> Tujuan: menetapkan aturan yang mencegah **double counting** dan menjaga
> **konsistensi saldo, cash flow, dan net worth**, sehingga tahap arsitektur &
> coding punya kontrak yang pasti.

---

## 0. Konsep Dasar & Konvensi Tanda

### 0.1 Akun (Account)
Setiap transaksi menyentuh satu atau dua **akun**. Setiap akun punya **tipe**
dan **klasifikasi neraca**:

| Tipe Akun | Klasifikasi | Arti Saldo | Contoh |
|-----------|-------------|-----------|--------|
| Cash | Asset | Uang tunai dimiliki | Dompet |
| Bank Account | Asset | Saldo di bank | BCA, Mandiri |
| E-wallet | Asset | Saldo e-wallet | GoPay, OVO, Dana |
| Credit Card | **Liability** | **Utang** (jumlah terutang) | Visa, Mastercard |

- **Asset account**: `balance` = uang yang dimiliki. Positif = punya uang.
- **Liability account (Credit Card)**: `balance` = **utang terutang**.
  Positif = jumlah yang harus dibayar. `balance = 0` berarti lunas.

### 0.2 Tipe Transaksi
`income`, `expense`, `transfer`, `refund`, `adjustment`. Setiap tipe punya efek
baku terhadap akun dan terhadap laporan (income/expense/cash flow).

### 0.3 Aturan Emas (Golden Rules)
1. **Transfer, pembayaran kartu kredit, refund bukan expense/income baru.**
2. **Setiap peristiwa ekonomi dihitung sekali** (no double counting).
3. **Expense diakui saat transaksi terjadi** (basis akrual), tidak menunggu
   pelunasan. Metode bayar (cash/bank/e-wallet/CC) tidak mengubah fakta bahwa
   itu expense.
4. **Net worth hanya berubah karena income, expense, atau adjustment** — tidak
   berubah karena transfer atau pembayaran kartu kredit.
5. **Semua nominal disimpan sebagai bilangan bulat terkecil (mis. rupiah) dan
   non-negatif.** Arah (+/−) ditentukan oleh tipe transaksi & peran akun, bukan
   oleh tanda nominal.

---

## 1. Income (Pemasukan)
- **Definisi:** uang masuk dari sumber eksternal (gaji, hadiah, penjualan).
- **Efek akun:** `account.balance += amount` (akun tujuan = asset).
- **Laporan:** `income += amount`. Menambah net worth.
- **Field:** `type=income`, `amount`, `to_account`, `category`, `date`, `note`.

## 2. Expense (Pengeluaran)
- **Definisi:** uang keluar untuk konsumsi/kewajiban (bukan pemindahan antar akun sendiri).
- **Efek akun:**
  - Dari akun asset: `account.balance -= amount`.
  - Dengan credit card: `creditcard.balance += amount` (utang bertambah).
- **Laporan:** `expense += amount`. Mengurangi net worth.
- **Field:** `type=expense`, `amount`, `from_account`, `category`, `date`, `note`.

## 3. Transfer (Pemindahan Antar Akun Sendiri)
- **Definisi:** memindahkan dana antar akun milik sendiri. **Bukan** income/expense.
- **Efek akun:** `from_account.balance -= amount`; `to_account.balance += amount`.
- **Laporan:** tidak mempengaruhi income/expense/net cash flow.
- **Net worth:** **tidak berubah** (jika keduanya asset).
- **Field:** `type=transfer`, `amount`, `from_account`, `to_account`, `date`, `note`.

> **Contoh wajib:** _"Transfer 2 juta dari BCA ke Mandiri"_
> BCA −2.000.000, Mandiri +2.000.000. Total asset tetap. **Bukan expense.**

## 4. Refund (Pengembalian Dana)
- **Definisi:** pembalikan (sebagian/penuh) dari expense yang sudah tercatat —
  uang kembali ke akun.
- **Efek akun:**
  - Refund ke akun asset: `account.balance += amount`.
  - Refund ke credit card: `creditcard.balance -= amount` (utang berkurang).
- **Laporan:** diperlakukan sebagai **contra-expense** (pengurang expense),
  **bukan income**. Ini menjaga kategori pengeluaran tetap akurat.
  - `net_expense = gross_expense − refunds`.
- **Net worth:** naik sebesar refund (kebalikan dari expense).
- **Keterkaitan:** refund sebaiknya menautkan `related_transaction_id` ke
  expense aslinya (opsional tapi direkomendasikan) untuk pelaporan & pencegahan
  salah hitung.
- **Field:** `type=refund`, `amount`, `to_account`, `category` (ikut expense asli), `related_transaction_id?`, `date`, `note`.

## 5. Adjustment (Penyesuaian/Koreksi Saldo)
- **Definisi:** koreksi manual agar saldo tercatat = saldo riil (rekonsiliasi),
  atau saldo awal saat membuat akun.
- **Efek akun:** `account.balance = target` → mencatat selisih
  `delta = target − current` sebagai entri adjustment.
- **Laporan:** dikeluarkan dari income/expense operasional; ditampilkan terpisah
  sebagai "adjustment". Mempengaruhi net worth sebesar `delta`.
- **Field:** `type=adjustment`, `account`, `delta` (boleh +/−), `reason`, `date`.
- **Catatan:** adjustment adalah "katup pengaman", bukan pengganti pencatatan
  transaksi normal. Gunakan hemat.

## 6. Cash
- Tipe akun **asset**. Perlakuan sama seperti akun asset lain.
- Karakter khusus: rawan tidak tercatat; adjustment lebih sering dipakai untuk
  merekonsiliasi tunai.

## 7. Bank Account
- Tipe akun **asset**. Saldo = dana tersedia di bank.

## 8. E-wallet
- Tipe akun **asset**. Perlakuan identik dengan bank account.
- Top-up e-wallet dari bank = **transfer** (asset→asset), bukan expense.

## 9. Credit Card (Kartu Kredit) — Pencegahan Double Counting
Credit card adalah **liability**. `balance` = utang terutang.

**Dua peristiwa berbeda yang TIDAK boleh dihitung dua kali:**

1. **Belanja pakai CC** → ini **expense** + utang bertambah.
   - `expense += amount`; `creditcard.balance += amount`.
2. **Bayar tagihan CC dari bank** → ini **transfer/pelunasan liability**, **bukan expense**.
   - `bank.balance −= amount`; `creditcard.balance −= amount`.

> **Contoh wajib:**
> - _"Beli laptop 10 juta pakai kartu kredit"_ → **Expense 10.000.000**;
>   CC.balance +10.000.000 (utang). Net worth −10.000.000.
> - _"Bayar kartu kredit 10 juta dari BCA"_ → **Bukan expense.**
>   BCA −10.000.000; CC.balance −10.000.000 (utang lunas). Net worth **tidak berubah**.
> - Total efek ekonomi laptop = **−10 juta sekali**, bukan −20 juta.

- **Cicilan/bunga/biaya CC:** bunga & biaya adalah **expense baru** (kategori
  Biaya/Bunga), menambah `creditcard.balance` dan `expense`.
- **Refund ke CC:** `creditcard.balance −= amount` (lihat §4).

## 10. Multiple Accounts
- Pengguna dapat memiliki banyak akun dari tipe apa pun.
- Setiap transaksi mereferensikan akun via ID.
- Total asset = Σ saldo akun asset; total liability = Σ saldo akun liability.
- Transfer hanya sah antar akun milik pengguna yang sama.

## 11. Balance (Saldo) — Formula
Untuk sebuah akun, saldo = akumulasi seluruh entri yang menyentuhnya:

```
balance(account) = starting_balance
  + Σ income.amount            (to = account)
  − Σ expense.amount           (from = account, asset)
  + Σ expense.amount           (on  = account, credit card → utang naik)
  − Σ transfer.amount          (from = account)
  + Σ transfer.amount          (to  = account)
  + Σ refund.amount            (to = account, asset)
  − Σ refund.amount            (on = account, credit card → utang turun)
  ± Σ adjustment.delta         (account)
```
Interpretasi:
- **Asset:** balance = uang tersedia.
- **Liability (CC):** balance = utang; pembayaran CC menurunkannya.

## 12. Net Cash Flow — Formula
Mengukur perubahan operasional selama periode. **Transfer & pembayaran CC dikecualikan.**

```
Total Income        = Σ income.amount            (dalam periode)
Total Expense       = Σ expense.amount           (dalam periode)
Total Refund        = Σ refund.amount            (dalam periode)
Net Expense         = Total Expense − Total Refund
Net Cash Flow       = Total Income − Net Expense
                    = Total Income − Total Expense + Total Refund
```
- Transfer = 0 pengaruh. Pembayaran CC = 0 pengaruh (itu transfer/pelunasan).
- Adjustment ditampilkan terpisah, tidak masuk Net Cash Flow operasional.

## 13. Net Worth — Formula
```
Total Assets      = Σ balance(account)  untuk semua akun bertipe asset
Total Liabilities = Σ balance(account)  untuk semua akun bertipe liability (CC)
Net Worth         = Total Assets − Total Liabilities
```
- Income menaikkan net worth; expense menurunkannya.
- Transfer & pembayaran CC **netral** terhadap net worth.
- Perubahan net worth periodik (tanpa adjustment eksternal) ≈ Net Cash Flow.

## 14. Recurring Transaction (Transaksi Berulang)
- **Definisi:** template transaksi yang berulang menurut jadwal (sewa, langganan, gaji).
- **Model:** `recurring_template { type, amount, account(s), category, frequency, next_date, active }`.
- **Aturan:** template **tidak** membuat transaksi secara diam-diam. Saat jatuh
  tempo, sistem **mengusulkan** transaksi untuk dikonfirmasi (konsisten dengan
  prinsip "draft dulu" di DECISIONS). Transaksi yang dihasilkan mengikuti aturan
  tipe-nya masing-masing.
- **Status:** konseptual — implementasi **Phase 3** (lihat PRODUCT_REQUIREMENTS).
  Didokumentasikan agar model data awal tidak menutup kemungkinan ini.

## 15. Duplicate Transaction (Deteksi Duplikat)
- **Tujuan:** mencegah pencatatan ganda tak sengaja (submit dobel, STT ganda),
  tanpa memblokir transaksi sah yang kebetulan mirip.
- **Kandidat duplikat** bila SEMUA benar:
  - `amount` sama (setelah normalisasi),
  - `type` sama,
  - akun yang terlibat sama,
  - selisih waktu ≤ **ambang** (default: **120 detik**; dapat dikonfigurasi),
  - (penguat opsional) kategori/deskripsi sangat mirip.
- **Aturan:** jangan auto-block dan jangan auto-merge. **Tandai & minta
  konfirmasi** ("Sepertinya ini sama dengan transaksi X, tetap simpan?").
- **Bukan duplikat:** dua transaksi identik yang sengaja (mis. beli 2 kopi
  terpisah) — karena itu konfirmasi manusia tetap menjadi penentu.

---

## CONTOH TRANSAKSI & EXPECTED RESULT

Asumsi saldo awal: BCA = 5.000.000; Mandiri = 1.000.000; Cash = 200.000; CC = 0 (lunas).

| # | Ucapan/Input | Tipe | Efek Akun | Income | Expense | Net Worth Δ |
|---|--------------|------|-----------|--------|---------|-------------|
| E1 | "Beli kopi 35 ribu pakai BCA" | expense | BCA −35.000 | 0 | +35.000 | −35.000 |
| E2 | "Gajian 8 juta masuk BCA" | income | BCA +8.000.000 | +8.000.000 | 0 | +8.000.000 |
| E3 | "Transfer 2 juta dari BCA ke Mandiri" | transfer | BCA −2.000.000; Mandiri +2.000.000 | 0 | 0 | 0 |
| E4 | "Top up GoPay 100 ribu dari BCA" | transfer | BCA −100.000; GoPay +100.000 | 0 | 0 | 0 |
| E5 | "Beli laptop 10 juta pakai kartu kredit" | expense | CC.balance +10.000.000 | 0 | +10.000.000 | −10.000.000 |
| E6 | "Bayar kartu kredit 10 juta dari BCA" | transfer(pelunasan) | BCA −10.000.000; CC.balance −10.000.000 | 0 | 0 | 0 |
| E7 | "Refund tas 300 ribu ke BCA" | refund | BCA +300.000 | 0 | −300.000 (contra) | +300.000 |
| E8 | "Sesuaikan saldo Cash jadi 150 ribu" (dari 200.000) | adjustment | Cash −50.000 (delta) | 0 | 0 | −50.000 |

**Hasil kumulatif setelah E1–E8:**
- BCA = 5.000.000 −35.000 +8.000.000 −2.000.000 −100.000 −10.000.000 +300.000 = **1.165.000**
- Mandiri = **3.000.000**; GoPay = **100.000**; Cash = **150.000**; CC = **0**
- Total Assets = 1.165.000 + 3.000.000 + 100.000 + 150.000 = **4.415.000**
- Total Liabilities = **0** → **Net Worth = 4.415.000**
- Periode: Income = 8.000.000; Gross Expense = 35.000 + 10.000.000 = 10.035.000;
  Refund = 300.000 → Net Expense = 9.735.000 → **Net Cash Flow = −1.735.000**

> Validasi kunci: laptop (E5) + bayar CC (E6) hanya menurunkan net worth **10 juta sekali**. ✔

---

## EDGE CASES
1. Expense tanpa akun disebut → butuh default akun atau konfirmasi.
2. Transfer ke akun yang sama → tolak (tidak valid).
3. Pembayaran CC melebihi utang → CC.balance jadi negatif (saldo lebih/kredit); tandai untuk konfirmasi.
4. Refund > expense asli → hanya boleh sampai jumlah expense terkait; kelebihan diperlakukan sebagai income atau ditolak (lihat Open Questions).
5. Refund tanpa expense asal yang jelas → izinkan sebagai contra-expense pada kategori terkait, tanpa `related_transaction_id`.
6. Mata uang non-IDR → di luar MVP; tolak/tandai (lihat Open Questions).
7. Nominal 0 atau negatif → tolak (arah ditentukan tipe, bukan tanda).
8. Saldo asset menjadi negatif (overdraft) → izinkan tetapi tandai peringatan (bank bisa saja negatif; e-wallet biasanya tidak).
9. Transaksi bertanggal masa depan → izinkan tapi tandai; pengaruhi laporan sesuai tanggalnya.
10. Multi-transaksi dalam satu ucapan → MVP tangani satu, sisanya ke Phase 2.
11. Menghapus/mengedit transaksi → seluruh saldo & laporan harus dihitung ulang secara konsisten (transaksi = sumber kebenaran, saldo = turunan).
12. Top-up/isi ulang e-wallet keliru dicatat sebagai expense → harus dikategorikan transfer.
13. Cashback dari transaksi → diperlakukan sebagai income atau contra-expense (lihat Open Questions).
14. Duplikat sah (dua kopi identik) → jangan blok; konfirmasi manusia menentukan.

---

## TEST CASES (untuk tahap implementasi nanti)
Ditulis sebagai spesifikasi; belum ada kode.

**Balance & tipe transaksi**
- TC-01: Expense dari asset mengurangi saldo akun tepat sebesar amount.
- TC-02: Income ke asset menambah saldo tepat sebesar amount.
- TC-03: Transfer A→B: A turun, B naik, total asset konstan; income=expense=0.
- TC-04: Transfer ke akun yang sama ditolak.

**Credit card / anti double counting**
- TC-05: Expense via CC menaikkan CC.balance & expense; saldo asset tidak berubah.
- TC-06: Bayar CC dari bank menurunkan bank & CC.balance; expense tidak bertambah.
- TC-07: Skenario E5+E6 → net worth turun tepat 10 juta (bukan 20 juta).
- TC-08: Bunga/biaya CC dicatat sebagai expense baru & menaikkan CC.balance.
- TC-09: Bayar CC melebihi utang → CC.balance negatif & ditandai.

**Refund**
- TC-10: Refund ke asset menambah saldo & mengurangi net_expense (bukan income).
- TC-11: Net Cash Flow memasukkan refund sebagai pengurang expense.
- TC-12: Refund ke CC menurunkan CC.balance.
- TC-13: Refund > expense terkait → sesuai kebijakan (tolak/limit/income).

**Adjustment**
- TC-14: Adjustment mengubah saldo ke target & mencatat delta; tidak masuk income/expense operasional.

**Formula agregat**
- TC-15: Net Cash Flow = Income − Expense + Refund (transfer & bayar CC = 0 pengaruh).
- TC-16: Net Worth = ΣAsset − ΣLiability, konsisten dengan seluruh entri.
- TC-17: Recompute: menghapus satu transaksi → semua saldo & laporan konsisten.

**Duplikat**
- TC-18: Dua expense sama (amount+akun+type) dalam ≤120 dtk → ditandai kandidat duplikat.
- TC-19: Selisih waktu > ambang → tidak ditandai.
- TC-20: Ditandai duplikat tetapi dikonfirmasi pengguna → tetap tersimpan.

**Validasi input**
- TC-21: Nominal 0/negatif ditolak.
- TC-22: Expense tanpa akun → minta akun/gunakan default.

---

## OPEN PRODUCT QUESTIONS (Financial)
Belum diputuskan — disertai rekomendasi. Mohon keputusan sebelum desain skema data.

1. **Refund melebihi expense terkait?**
   → _Rekomendasi:_ batasi refund maksimal sebesar expense terkait; kelebihan
   diperlakukan sebagai income terpisah dengan konfirmasi.
2. **Cashback / reward diperlakukan sebagai apa?**
   → _Rekomendasi:_ default **contra-expense** pada kategori terkait; opsi income bila dari program poin.
3. **Multi-currency?**
   → _Rekomendasi:_ **IDR-only** untuk MVP; tandai/tolak non-IDR. Multi-currency Phase 3.
4. **Basis pelaporan: akrual (saat transaksi) atau kas (saat dibayar)?**
   → _Rekomendasi:_ **akrual** untuk expense (sudah dipakai di dokumen ini) —
   sesuai model mental "aku belanja X", dan mencegah double counting CC.
5. **Overdraft/saldo negatif akun asset?**
   → _Rekomendasi:_ izinkan dengan peringatan (bank), tandai untuk e-wallet/cash.
6. **Sumber kebenaran saldo?**
   → _Rekomendasi:_ **transaksi = sumber kebenaran**, saldo = nilai turunan yang
   dihitung/di-cache; hindari menyimpan saldo sebagai satu-satunya sumber.

---

_Dokumen ini menjadi kontrak logika keuangan untuk tahap arsitektur & test.
Perubahan aturan harus dicatat di `docs/DECISIONS.md`._
