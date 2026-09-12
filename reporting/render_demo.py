"""Seed contoh + render docs/prototype/dashboard.html dari Financial Engine.

Jalankan: ``python3 -m reporting.render_demo``
Halaman hasil hanya MENAMPILKAN angka yang dihitung engine.
"""

from __future__ import annotations

import os
from datetime import datetime

from financial_engine import AccountType, FinancialEngine

from .dashboard import build_dashboard, render_dashboard_html, transaction_views


def seed() -> FinancialEngine:
    e = FinancialEngine()
    bca = e.add_account("BCA", AccountType.BANK, starting_balance=5_000_000)
    mandiri = e.add_account("Mandiri", AccountType.BANK, starting_balance=1_000_000)
    cash = e.add_account("Cash", AccountType.CASH, starting_balance=200_000)
    gopay = e.add_account("GoPay", AccountType.EWALLET, starting_balance=0)
    cc = e.add_account("Visa", AccountType.CREDIT_CARD, starting_balance=0)

    def dt(day, hour=10):
        return datetime(2026, 9, day, hour, 0, 0)

    e.create_income(8_000_000, bca.id, category="Gaji", occurred_at=dt(1))
    e.create_transfer(100_000, bca.id, gopay.id, occurred_at=dt(1, 11))  # top up
    e.create_expense(35_000, bca.id, category="Makanan & Minuman", occurred_at=dt(2))
    e.create_expense(50_000, bca.id, category="Makanan & Minuman", occurred_at=dt(3))
    e.create_expense(100_000, bca.id, category="Transport", occurred_at=dt(4))
    e.create_expense(5_000, cash.id, category="Transport", occurred_at=dt(4, 12))
    e.create_expense(50_000, gopay.id, category="Tagihan", occurred_at=dt(4, 13))
    e.create_expense(10_000_000, cc.id, category="Elektronik", occurred_at=dt(5))
    e.create_transfer(10_000_000, bca.id, cc.id, occurred_at=dt(6))  # bayar CC
    e.create_refund(300_000, bca.id, category="Belanja", occurred_at=dt(7))
    e.create_transfer(2_000_000, bca.id, mandiri.id, occurred_at=dt(8))
    return e


def main() -> str:
    engine = seed()
    data = build_dashboard(engine, 2026, 9)
    html = render_dashboard_html(data, transaction_views(engine))
    out = os.path.join(os.path.dirname(__file__), "..", "docs", "prototype", "dashboard.html")
    out = os.path.abspath(out)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    return out


if __name__ == "__main__":
    print("ditulis:", main())
