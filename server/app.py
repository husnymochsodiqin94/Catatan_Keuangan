"""HTTP server stdlib: API JSON (multi-user) + menyajikan PWA statis.

Jalankan: ``python3 -m server.app`` lalu buka http://127.0.0.1:8000
Env opsional: CATATAN_DB (path SQLite), HOST, PORT.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from financial_engine import ValidationError

from . import service
from .service import AuthError
from .storage import Storage

WEBAPP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "webapp"))
_STORAGE = Storage(os.environ.get("CATATAN_DB", "data.db"))

_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml",
    ".webmanifest": "application/manifest+json", ".json": "application/json",
    ".png": "image/png", ".ico": "image/x-icon",
}
_PUBLIC = {"/api/health", "/api/auth/register", "/api/auth/login"}


def _int(qs: dict, key: str):
    v = qs.get(key, [None])[0]
    return int(v) if v not in (None, "") else None


class Handler(BaseHTTPRequestHandler):
    server_version = "CatatanKeuangan/0.2"

    # ---- util ------------------------------------------------------- #
    def _json(self, obj, status: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return {}

    def _token(self) -> str:
        tok = self.headers.get("X-Token")
        if not tok:
            auth = self.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                tok = auth[7:]
        return tok or ""

    def _require_user(self, path: str):
        """Kembalikan user_id untuk endpoint terproteksi; None (401 terkirim) bila gagal."""
        if path in _PUBLIC:
            return "__public__"
        user_id = _STORAGE.get_session_user(self._token())
        if not user_id:
            self._json({"error": "unauthorized"}, 401)
            return None
        return user_id

    def log_message(self, *args):
        pass

    # ---- dispatch --------------------------------------------------- #
    def do_GET(self):
        parsed = urlparse(self.path)
        path, qs = parsed.path, parse_qs(parsed.query)
        try:
            if path == "/api/health":
                return self._json({"ok": True})
            if path.startswith("/api/"):
                uid = self._require_user(path)
                if uid is None:
                    return
                if path == "/api/auth/me":
                    return self._json(service.current_user(_STORAGE, uid))
                if path == "/api/accounts":
                    return self._json(service.list_accounts(_STORAGE, uid))
                if path == "/api/summary":
                    return self._json(service.summary(_STORAGE, uid, _int(qs, "year"), _int(qs, "month")))
                if path == "/api/transactions":
                    return self._json(service.list_transactions(
                        _STORAGE, uid, type=qs.get("type", [None])[0],
                        text=qs.get("q", [None])[0], account_id=qs.get("account_id", [None])[0]))
                if path == "/api/settings":
                    return self._json(service.get_settings(_STORAGE, uid))
                if path == "/api/budget":
                    return self._json(service.budget_status(_STORAGE, uid))
                return self._json({"error": "not found"}, 404)
            return self._serve_static(path)
        except (AuthError,) as exc:
            return self._json({"error": str(exc)}, 401)
        except (ValidationError, ValueError) as exc:
            return self._json({"error": str(exc)}, 400)
        except Exception:
            return self._json({"error": "kesalahan server"}, 500)

    def do_POST(self):
        path = urlparse(self.path).path
        data = self._read_json()
        try:
            if path == "/api/auth/register":
                return self._json(service.register(
                    _STORAGE, data.get("email"), data.get("password"), data.get("display_name", "")), 201)
            if path == "/api/auth/login":
                return self._json(service.login(_STORAGE, data.get("email"), data.get("password")))
            uid = self._require_user(path)
            if uid is None:
                return
            if path == "/api/auth/logout":
                return self._json(service.logout(_STORAGE, self._token()))
            if path == "/api/accounts":
                return self._json(service.create_account(
                    _STORAGE, uid, data.get("name"), data.get("type"),
                    int(data.get("starting_balance") or 0)), 201)
            if path == "/api/parse":
                return self._json(service.parse_text(_STORAGE, uid, data.get("text", "")))
            if path == "/api/transactions":
                return self._json(service.create_transaction(_STORAGE, uid, data), 201)
            if path == "/api/settings":
                return self._json(service.update_settings(_STORAGE, uid, data))
            if path == "/api/alerts/send":
                return self._json(service.send_alerts(_STORAGE, uid))
            return self._json({"error": "not found"}, 404)
        except (AuthError,) as exc:
            return self._json({"error": str(exc)}, 401)
        except (ValidationError, ValueError) as exc:
            return self._json({"error": str(exc)}, 400)
        except Exception:
            return self._json({"error": "kesalahan server"}, 500)

    def do_DELETE(self):
        path = urlparse(self.path).path
        try:
            uid = self._require_user(path)
            if uid is None:
                return
            if path.startswith("/api/transactions/"):
                return self._json(service.delete_transaction(_STORAGE, uid, path[len("/api/transactions/"):]))
            if path.startswith("/api/accounts/"):
                return self._json(service.delete_account(_STORAGE, uid, path[len("/api/accounts/"):]))
            return self._json({"error": "not found"}, 404)
        except (ValidationError, ValueError) as exc:
            return self._json({"error": str(exc)}, 400)
        except Exception:
            return self._json({"error": "kesalahan server"}, 500)

    def do_PATCH(self):
        path = urlparse(self.path).path
        data = self._read_json()
        try:
            uid = self._require_user(path)
            if uid is None:
                return
            if path.startswith("/api/transactions/"):
                return self._json(service.edit_transaction(_STORAGE, uid, path[len("/api/transactions/"):], data))
            if path.startswith("/api/accounts/"):
                return self._json(service.update_account(_STORAGE, uid, path[len("/api/accounts/"):], data))
            return self._json({"error": "not found"}, 404)
        except (ValidationError, ValueError) as exc:
            return self._json({"error": str(exc)}, 400)
        except Exception:
            return self._json({"error": "kesalahan server"}, 500)

    # ---- static ----------------------------------------------------- #
    def _serve_static(self, path: str) -> None:
        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        full = os.path.abspath(os.path.join(WEBAPP_DIR, rel))
        if not full.startswith(WEBAPP_DIR + os.sep) and full != WEBAPP_DIR:
            return self._json({"error": "not found"}, 404)
        if not os.path.isfile(full):
            full = os.path.join(WEBAPP_DIR, "index.html")
            if not os.path.isfile(full):
                return self._json({"error": "webapp belum tersedia"}, 404)
        ext = os.path.splitext(full)[1]
        with open(full, "rb") as fh:
            body = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", _CONTENT_TYPES.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"AI Financial Assistant berjalan di http://{host}:{port}  (Ctrl+C untuk berhenti)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nberhenti.")
        httpd.server_close()


if __name__ == "__main__":
    main()
