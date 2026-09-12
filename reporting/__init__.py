"""Reporting/presenter layer untuk UI.

Menyusun data dashboard & history HANYA dari angka yang dihitung Financial
Engine. Lapisan ini tidak melakukan perhitungan finansial sendiri — hanya
memetakan, mengurutkan, dan memformat untuk tampilan.
"""

from .dashboard import DashboardData, build_dashboard, render_dashboard_html, transaction_views

__all__ = [
    "DashboardData",
    "build_dashboard",
    "transaction_views",
    "render_dashboard_html",
]
