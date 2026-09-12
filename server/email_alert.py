"""Pengiriman alert via email (stdlib smtplib).

Aktif hanya bila dikonfigurasi lewat env (SMTP_HOST, SMTP_FROM, dsb). Tanpa
konfigurasi, ``is_configured()`` False dan alert cukup ditampilkan in-app.
Tidak ada dependency pihak ketiga.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Optional


def is_configured() -> bool:
    return bool(os.environ.get("SMTP_HOST") and os.environ.get("SMTP_FROM"))


def send_email(to: str, subject: str, body: str) -> None:
    """Kirim satu email teks. Raise RuntimeError bila belum dikonfigurasi."""
    if not is_configured():
        raise RuntimeError("email belum dikonfigurasi (set SMTP_HOST & SMTP_FROM)")
    if not to:
        raise ValueError("alamat email tujuan kosong")

    msg = EmailMessage()
    msg["From"] = os.environ["SMTP_FROM"]
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")
    use_ssl = os.environ.get("SMTP_SSL", "").lower() in ("1", "true", "yes")

    if use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=15) as s:
            if user:
                s.login(user, password or "")
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=15) as s:
            s.starttls()
            if user:
                s.login(user, password or "")
            s.send_message(msg)
