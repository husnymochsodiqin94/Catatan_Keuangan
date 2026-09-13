"""Taksonomi kategori keuangan (sumber kebenaran tunggal).

Listing kategori & subkategori Pemasukan/Pengeluaran (id-ID) beserta keyword
untuk deteksi otomatis oleh parser. Dipakai bersama oleh:
- ``nlp.parser`` (memetakan teks -> kategori/subkategori),
- ``server.service`` (endpoint ``/api/categories`` -> dropdown terkelompok).

Menambah kategori/subkategori/keyword cukup di file ini.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

# --------------------------------------------------------------------- #
# Listing kategori (urutan dipertahankan untuk tampilan)
# --------------------------------------------------------------------- #
INCOME: List[Dict[str, object]] = [
    {"category": "Pemasukan Aktif",
     "subcategories": ["Gaji & Tunjangan", "Bonus, THR & Komisi", "Freelance & Proyek"]},
    {"category": "Pemasukan Pasif & Investasi",
     "subcategories": ["Dividen & Capital Gain", "Bunga & Kupon Obligasi", "Sewa & Properti"]},
    {"category": "Pemasukan Lainnya",
     "subcategories": ["Cashback, Refund & Hadiah", "Transfer Masuk / Patungan",
                       "Penjualan Barang Bekas"]},
]

EXPENSE: List[Dict[str, object]] = [
    {"category": "Makanan & Minuman",
     "subcategories": ["Makan Harian & Sembako", "Restoran & Cafe",
                       "Pesan-Antar", "Camilan & Snack"]},
    {"category": "Transportasi & Mobilitas",
     "subcategories": ["BBM & Bahan Bakar", "Transportasi Umum & Online",
                       "Parkir & Tol", "Perawatan Kendaraan"]},
    {"category": "Tagihan & Utilitas",
     "subcategories": ["Listrik, Air & Gas", "Internet, Pulsa & Data",
                       "Sewa Tempat Tinggal / Kost", "Langganan Digital"]},
    {"category": "Kesehatan & Olahraga",
     "subcategories": ["Obat, Apotek & Medis", "Olahraga & Membership",
                       "Peralatan Olahraga & Apparel"]},
    {"category": "Gaya Hidup & Hiburan",
     "subcategories": ["Bioskop, Konser & Rekreasi", "Hobi & Gaming",
                       "Nongkrong & Acara Sosial"]},
    {"category": "Belanja Pribadi",
     "subcategories": ["Pakaian & Aksesoris", "Elektronik & Gadget", "Perawatan Diri"]},
    {"category": "Sosial, Keluarga & Keagamaan",
     "subcategories": ["Zakat, Infaq & Donasi", "Orang Tua & Keluarga", "Kondangan & Hadiah"]},
    {"category": "Finansial & Kewajiban",
     "subcategories": ["Cicilan & Hutang", "Asuransi & Pajak"]},
]


def categories_for(txn_type: Optional[str]) -> List[Dict[str, object]]:
    """Listing kategori sesuai jenis transaksi (income -> pemasukan, lainnya -> pengeluaran)."""
    return INCOME if txn_type == "income" else EXPENSE


def grouped() -> Dict[str, List[Dict[str, object]]]:
    """Bentuk untuk API/dropdown."""
    return {"income": INCOME, "expense": EXPENSE}


# --------------------------------------------------------------------- #
# Keyword -> (kategori, subkategori). Urutan: paling spesifik lebih dulu.
# --------------------------------------------------------------------- #
_RULES: List[Tuple[str, str, str]] = [
    # --- Pengeluaran: Makanan & Minuman ---
    ("gofood", "Makanan & Minuman", "Pesan-Antar"),
    ("grabfood", "Makanan & Minuman", "Pesan-Antar"),
    ("shopeefood", "Makanan & Minuman", "Pesan-Antar"),
    ("kopi", "Makanan & Minuman", "Restoran & Cafe"),
    ("starbucks", "Makanan & Minuman", "Restoran & Cafe"),
    ("cafe", "Makanan & Minuman", "Restoran & Cafe"),
    ("kafe", "Makanan & Minuman", "Restoran & Cafe"),
    ("restoran", "Makanan & Minuman", "Restoran & Cafe"),
    ("resto", "Makanan & Minuman", "Restoran & Cafe"),
    ("bakmi", "Makanan & Minuman", "Restoran & Cafe"),
    ("warteg", "Makanan & Minuman", "Makan Harian & Sembako"),
    ("sembako", "Makanan & Minuman", "Makan Harian & Sembako"),
    ("beras", "Makanan & Minuman", "Makan Harian & Sembako"),
    ("sayur", "Makanan & Minuman", "Makan Harian & Sembako"),
    ("nasi", "Makanan & Minuman", "Makan Harian & Sembako"),
    ("martabak", "Makanan & Minuman", "Camilan & Snack"),
    ("snack", "Makanan & Minuman", "Camilan & Snack"),
    ("camilan", "Makanan & Minuman", "Camilan & Snack"),
    ("cemilan", "Makanan & Minuman", "Camilan & Snack"),
    ("roti", "Makanan & Minuman", "Camilan & Snack"),
    ("jus", "Makanan & Minuman", "Camilan & Snack"),
    ("makanan", "Makanan & Minuman", "Makan Harian & Sembako"),
    ("makan", "Makanan & Minuman", "Makan Harian & Sembako"),
    ("minum", "Makanan & Minuman", "Makan Harian & Sembako"),
    ("jajan", "Makanan & Minuman", "Camilan & Snack"),
    # --- Pengeluaran: Transportasi & Mobilitas ---
    ("pertamax", "Transportasi & Mobilitas", "BBM & Bahan Bakar"),
    ("pertalite", "Transportasi & Mobilitas", "BBM & Bahan Bakar"),
    ("solar", "Transportasi & Mobilitas", "BBM & Bahan Bakar"),
    ("bensin", "Transportasi & Mobilitas", "BBM & Bahan Bakar"),
    ("bbm", "Transportasi & Mobilitas", "BBM & Bahan Bakar"),
    ("parkir", "Transportasi & Mobilitas", "Parkir & Tol"),
    ("tol", "Transportasi & Mobilitas", "Parkir & Tol"),
    ("e-toll", "Transportasi & Mobilitas", "Parkir & Tol"),
    ("etoll", "Transportasi & Mobilitas", "Parkir & Tol"),
    ("ganti oli", "Transportasi & Mobilitas", "Perawatan Kendaraan"),
    ("servis", "Transportasi & Mobilitas", "Perawatan Kendaraan"),
    ("bengkel", "Transportasi & Mobilitas", "Perawatan Kendaraan"),
    ("cuci mobil", "Transportasi & Mobilitas", "Perawatan Kendaraan"),
    ("cuci motor", "Transportasi & Mobilitas", "Perawatan Kendaraan"),
    ("grab", "Transportasi & Mobilitas", "Transportasi Umum & Online"),
    ("gojek", "Transportasi & Mobilitas", "Transportasi Umum & Online"),
    ("ojek", "Transportasi & Mobilitas", "Transportasi Umum & Online"),
    ("mrt", "Transportasi & Mobilitas", "Transportasi Umum & Online"),
    ("krl", "Transportasi & Mobilitas", "Transportasi Umum & Online"),
    ("kai", "Transportasi & Mobilitas", "Transportasi Umum & Online"),
    ("busway", "Transportasi & Mobilitas", "Transportasi Umum & Online"),
    ("transjakarta", "Transportasi & Mobilitas", "Transportasi Umum & Online"),
    ("kereta", "Transportasi & Mobilitas", "Transportasi Umum & Online"),
    ("kcic", "Transportasi & Mobilitas", "Transportasi Umum & Online"),
    # --- Pengeluaran: Tagihan & Utilitas ---
    ("token listrik", "Tagihan & Utilitas", "Listrik, Air & Gas"),
    ("listrik", "Tagihan & Utilitas", "Listrik, Air & Gas"),
    ("pln", "Tagihan & Utilitas", "Listrik, Air & Gas"),
    ("pdam", "Tagihan & Utilitas", "Listrik, Air & Gas"),
    ("lpg", "Tagihan & Utilitas", "Listrik, Air & Gas"),
    ("paket data", "Tagihan & Utilitas", "Internet, Pulsa & Data"),
    ("kuota", "Tagihan & Utilitas", "Internet, Pulsa & Data"),
    ("pulsa", "Tagihan & Utilitas", "Internet, Pulsa & Data"),
    ("indihome", "Tagihan & Utilitas", "Internet, Pulsa & Data"),
    ("internet", "Tagihan & Utilitas", "Internet, Pulsa & Data"),
    ("wifi", "Tagihan & Utilitas", "Internet, Pulsa & Data"),
    ("kost", "Tagihan & Utilitas", "Sewa Tempat Tinggal / Kost"),
    ("kos", "Tagihan & Utilitas", "Sewa Tempat Tinggal / Kost"),
    ("kontrakan", "Tagihan & Utilitas", "Sewa Tempat Tinggal / Kost"),
    ("netflix", "Tagihan & Utilitas", "Langganan Digital"),
    ("spotify", "Tagihan & Utilitas", "Langganan Digital"),
    ("langganan", "Tagihan & Utilitas", "Langganan Digital"),
    ("subscription", "Tagihan & Utilitas", "Langganan Digital"),
    # --- Pengeluaran: Kesehatan & Olahraga ---
    ("apotek", "Kesehatan & Olahraga", "Obat, Apotek & Medis"),
    ("obat", "Kesehatan & Olahraga", "Obat, Apotek & Medis"),
    ("dokter", "Kesehatan & Olahraga", "Obat, Apotek & Medis"),
    ("klinik", "Kesehatan & Olahraga", "Obat, Apotek & Medis"),
    ("vitamin", "Kesehatan & Olahraga", "Obat, Apotek & Medis"),
    ("sepatu lari", "Kesehatan & Olahraga", "Peralatan Olahraga & Apparel"),
    ("raket", "Kesehatan & Olahraga", "Peralatan Olahraga & Apparel"),
    ("jersey", "Kesehatan & Olahraga", "Peralatan Olahraga & Apparel"),
    ("sewa lapangan", "Kesehatan & Olahraga", "Olahraga & Membership"),
    ("lapangan", "Kesehatan & Olahraga", "Olahraga & Membership"),
    ("futsal", "Kesehatan & Olahraga", "Olahraga & Membership"),
    ("mini soccer", "Kesehatan & Olahraga", "Olahraga & Membership"),
    ("mini soker", "Kesehatan & Olahraga", "Olahraga & Membership"),
    ("soccer", "Kesehatan & Olahraga", "Olahraga & Membership"),
    ("soker", "Kesehatan & Olahraga", "Olahraga & Membership"),
    ("sepak bola", "Kesehatan & Olahraga", "Olahraga & Membership"),
    ("sepakbola", "Kesehatan & Olahraga", "Olahraga & Membership"),
    ("bola", "Kesehatan & Olahraga", "Olahraga & Membership"),
    ("badminton", "Kesehatan & Olahraga", "Olahraga & Membership"),
    ("bulutangkis", "Kesehatan & Olahraga", "Olahraga & Membership"),
    ("basket", "Kesehatan & Olahraga", "Olahraga & Membership"),
    ("voli", "Kesehatan & Olahraga", "Olahraga & Membership"),
    ("tenis", "Kesehatan & Olahraga", "Olahraga & Membership"),
    ("gym", "Kesehatan & Olahraga", "Olahraga & Membership"),
    ("fitness", "Kesehatan & Olahraga", "Olahraga & Membership"),
    ("renang", "Kesehatan & Olahraga", "Olahraga & Membership"),
    # --- Pengeluaran: Gaya Hidup & Hiburan ---
    ("bioskop", "Gaya Hidup & Hiburan", "Bioskop, Konser & Rekreasi"),
    ("xxi", "Gaya Hidup & Hiburan", "Bioskop, Konser & Rekreasi"),
    ("cgv", "Gaya Hidup & Hiburan", "Bioskop, Konser & Rekreasi"),
    ("konser", "Gaya Hidup & Hiburan", "Bioskop, Konser & Rekreasi"),
    ("wisata", "Gaya Hidup & Hiburan", "Bioskop, Konser & Rekreasi"),
    ("rekreasi", "Gaya Hidup & Hiburan", "Bioskop, Konser & Rekreasi"),
    ("steam", "Gaya Hidup & Hiburan", "Hobi & Gaming"),
    ("game", "Gaya Hidup & Hiburan", "Hobi & Gaming"),
    ("gaming", "Gaya Hidup & Hiburan", "Hobi & Gaming"),
    ("buku", "Gaya Hidup & Hiburan", "Hobi & Gaming"),
    ("mainan", "Gaya Hidup & Hiburan", "Hobi & Gaming"),
    ("nongkrong", "Gaya Hidup & Hiburan", "Nongkrong & Acara Sosial"),
    ("arisan", "Gaya Hidup & Hiburan", "Nongkrong & Acara Sosial"),
    ("reuni", "Gaya Hidup & Hiburan", "Nongkrong & Acara Sosial"),
    # --- Pengeluaran: Belanja Pribadi ---
    ("skincare", "Belanja Pribadi", "Perawatan Diri"),
    ("shampoo", "Belanja Pribadi", "Perawatan Diri"),
    ("potong rambut", "Belanja Pribadi", "Perawatan Diri"),
    ("salon", "Belanja Pribadi", "Perawatan Diri"),
    ("parfum", "Belanja Pribadi", "Perawatan Diri"),
    ("monitor", "Belanja Pribadi", "Elektronik & Gadget"),
    ("charger", "Belanja Pribadi", "Elektronik & Gadget"),
    ("earphone", "Belanja Pribadi", "Elektronik & Gadget"),
    ("headset", "Belanja Pribadi", "Elektronik & Gadget"),
    ("laptop", "Belanja Pribadi", "Elektronik & Gadget"),
    ("keyboard", "Belanja Pribadi", "Elektronik & Gadget"),
    ("baju", "Belanja Pribadi", "Pakaian & Aksesoris"),
    ("celana", "Belanja Pribadi", "Pakaian & Aksesoris"),
    ("kaos", "Belanja Pribadi", "Pakaian & Aksesoris"),
    ("jaket", "Belanja Pribadi", "Pakaian & Aksesoris"),
    ("uniqlo", "Belanja Pribadi", "Pakaian & Aksesoris"),
    ("sepatu", "Belanja Pribadi", "Pakaian & Aksesoris"),
    ("tas", "Belanja Pribadi", "Pakaian & Aksesoris"),
    # --- Pengeluaran: Sosial, Keluarga & Keagamaan ---
    ("zakat", "Sosial, Keluarga & Keagamaan", "Zakat, Infaq & Donasi"),
    ("infaq", "Sosial, Keluarga & Keagamaan", "Zakat, Infaq & Donasi"),
    ("infak", "Sosial, Keluarga & Keagamaan", "Zakat, Infaq & Donasi"),
    ("sedekah", "Sosial, Keluarga & Keagamaan", "Zakat, Infaq & Donasi"),
    ("donasi", "Sosial, Keluarga & Keagamaan", "Zakat, Infaq & Donasi"),
    ("qurban", "Sosial, Keluarga & Keagamaan", "Zakat, Infaq & Donasi"),
    ("kado", "Sosial, Keluarga & Keagamaan", "Kondangan & Hadiah"),
    ("kondangan", "Sosial, Keluarga & Keagamaan", "Kondangan & Hadiah"),
    ("nikahan", "Sosial, Keluarga & Keagamaan", "Kondangan & Hadiah"),
    ("amplop", "Sosial, Keluarga & Keagamaan", "Kondangan & Hadiah"),
    # --- Pengeluaran: Finansial & Kewajiban ---
    ("kartu kredit", "Finansial & Kewajiban", "Cicilan & Hutang"),
    ("paylater", "Finansial & Kewajiban", "Cicilan & Hutang"),
    ("cicilan", "Finansial & Kewajiban", "Cicilan & Hutang"),
    ("hutang", "Finansial & Kewajiban", "Cicilan & Hutang"),
    ("utang", "Finansial & Kewajiban", "Cicilan & Hutang"),
    ("bpjs", "Finansial & Kewajiban", "Asuransi & Pajak"),
    ("asuransi", "Finansial & Kewajiban", "Asuransi & Pajak"),
    ("pajak", "Finansial & Kewajiban", "Asuransi & Pajak"),
    ("stnk", "Finansial & Kewajiban", "Asuransi & Pajak"),
    # --- Pemasukan ---
    ("gajian", "Pemasukan Aktif", "Gaji & Tunjangan"),
    ("gaji", "Pemasukan Aktif", "Gaji & Tunjangan"),
    ("tunjangan", "Pemasukan Aktif", "Gaji & Tunjangan"),
    ("bonus", "Pemasukan Aktif", "Bonus, THR & Komisi"),
    ("thr", "Pemasukan Aktif", "Bonus, THR & Komisi"),
    ("komisi", "Pemasukan Aktif", "Bonus, THR & Komisi"),
    ("freelance", "Pemasukan Aktif", "Freelance & Proyek"),
    ("proyek", "Pemasukan Aktif", "Freelance & Proyek"),
    ("dividen", "Pemasukan Pasif & Investasi", "Dividen & Capital Gain"),
    ("reksadana", "Pemasukan Pasif & Investasi", "Dividen & Capital Gain"),
    ("bunga deposito", "Pemasukan Pasif & Investasi", "Bunga & Kupon Obligasi"),
    ("deposito", "Pemasukan Pasif & Investasi", "Bunga & Kupon Obligasi"),
    ("obligasi", "Pemasukan Pasif & Investasi", "Bunga & Kupon Obligasi"),
    ("uang sewa", "Pemasukan Pasif & Investasi", "Sewa & Properti"),
    ("sewa kontrakan", "Pemasukan Pasif & Investasi", "Sewa & Properti"),
    ("cashback", "Pemasukan Lainnya", "Cashback, Refund & Hadiah"),
    ("hadiah lomba", "Pemasukan Lainnya", "Cashback, Refund & Hadiah"),
    ("patungan", "Pemasukan Lainnya", "Transfer Masuk / Patungan"),
    ("thrift", "Pemasukan Lainnya", "Penjualan Barang Bekas"),
]

# Pra-kompilasi regex word-boundary untuk tiap keyword.
_COMPILED: List[Tuple[re.Pattern, str, str]] = [
    (re.compile(rf"\b{re.escape(kw)}\b"), cat, sub) for kw, cat, sub in _RULES
]


def match(low_text: str) -> Optional[Tuple[str, str]]:
    """Kembalikan (kategori, subkategori) pertama yang cocok, atau None."""
    for pat, cat, sub in _COMPILED:
        if pat.search(low_text):
            return cat, sub
    return None


_CAT_TYPE: Dict[str, str] = {}
for _g in INCOME:
    _CAT_TYPE[str(_g["category"])] = "income"
for _g in EXPENSE:
    _CAT_TYPE[str(_g["category"])] = "expense"


def type_of(category: Optional[str]) -> Optional[str]:
    """'income' / 'expense' untuk kategori utama; None bila tak dikenal."""
    return _CAT_TYPE.get(category or "")
