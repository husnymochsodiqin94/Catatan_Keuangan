"""HTTP server stdlib: API JSON + menyajikan PWA statis (satu origin).

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
from .storage import Storage

WEBAPP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "webapp"))
_STORAGE = Storage(os.environ.get("CATATAN_DB", "data.db"))
_TOKEN = os.environ.get("CATATAN_TOKEN")  # bila diset, API butuh token (untuk deploy)

_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml",
    ".webmanifest": "application/manifest+json", ".json": "application/json",
    ".png": "image/png", ".ico": "image/x-icon",
}


def _int(qs: dict, key: str):
    v = qs.get(key, [None])[0]
    return int(v) if v not in (None, "") else None


class Handler(BaseHTTPRequestHandler):
    server_version = "CatatanKeuangan/0.1"

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

    def log_message(self, *args):  # senyapkan log default
        pass

    def _auth_ok(self, path: str) -> bool:
        """Bila CATATAN_TOKEN diset, endpoint /api (selain health) butuh token."""
        if not _TOKEN or path == "/api/health" or not path.startswith("/api/"):
            return True
        tok = self.headers.get("X-Token") or parse_qs(urlparse(self.path).query).get("token", [None])[0]
        if tok == _TOKEN:
            return True
        self._json({"error": "unauthorized"}, 401)
        return False

    # ---- dispatch --------------------------------------------------- #
    def do_GET(self):
        parsed = urlparse(self.path)
        path, qs = parsed.path, parse_qs(parsed.query)
        if not self._auth_ok(path):
            return
        try:
            if path == "/api/health":
                return self._json({"ok": True})
            if path == "/api/accounts":
                return self._json(service.list_accounts(_STORAGE))
            if path == "/api/summary":
                return self._json(service.summary(_STORAGE, _int(qs, "year"), _int(qs, "month")))
            if path == "/api/transactions":
                return self._json(service.list_transactions(
                    _STORAGE, type=qs.get("type", [None])[0],
                    text=qs.get("q", [None])[0], account_id=qs.get("account_id", [None])[0]))
            if path == "/api/settings":
                return self._json(service.get_settings(_STORAGE))
            if path == "/api/budget":
                return self._json(service.budget_status(_STORAGE))
            if path.startswith("/api/"):
                return self._json({"error": "not found"}, 404)
            return self._serve_static(path)
        except (ValidationError, ValueError) as exc:
            return self._json({"error": str(exc)}, 400)
        except Exception as exc:  # jangan bocorkan detail internal
            return self._json({"error": "kesalahan server"}, 500)

    def do_POST(self):
        path = urlparse(self.path).path
        if not self._auth_ok(path):
            return
        data = self._read_json()
        try:
            if path == "/api/accounts":
                return self._json(service.create_account(
                    _STORAGE, data.get("name"), data.get("type"),
                    int(data.get("starting_balance") or 0)), 201)
            if path == "/api/parse":
                return self._json(service.parse_text(_STORAGE, data.get("text", "")))
            if path == "/api/transactions":
                return self._json(service.create_transaction(_STORAGE, data), 201)
            if path == "/api/settings":
                return self._json(service.update_settings(_STORAGE, data))
            if path == "/api/alerts/send":
                return self._json(service.send_alerts(_STORAGE))
            return self._json({"error": "not found"}, 404)
        except (ValidationError, ValueError) as exc:
            return self._json({"error": str(exc)}, 400)
        except Exception:
            return self._json({"error": "kesalahan server"}, 500)

    def do_DELETE(self):
        path = urlparse(self.path).path
        if not self._auth_ok(path):
            return
        try:
            prefix = "/api/transactions/"
            if path.startswith(prefix):
                tx_id = path[len(prefix):]
                return self._json(service.delete_transaction(_STORAGE, tx_id))
            return self._json({"error": "not found"}, 404)
        except (ValidationError, ValueError) as exc:
            return self._json({"error": str(exc)}, 400)
        except Exception:
            return self._json({"error": "kesalahan server"}, 500)

    def do_PATCH(self):
        path = urlparse(self.path).path
        if not self._auth_ok(path):
            return
        data = self._read_json()
        try:
            prefix = "/api/transactions/"
            if path.startswith(prefix):
                tx_id = path[len(prefix):]
                return self._json(service.edit_transaction(_STORAGE, tx_id, data))
            return self._json({"error": "not found"}, 404)
        except (ValidationError, ValueError) as exc:
            return self._json({"error": str(exc)}, 400)
        except Exception:
            return self._json({"error": "kesalahan server"}, 500)

    # ---- static ----------------------------------------------------- #
    def _serve_static(self, path: str) -> None:
        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        full = os.path.abspath(os.path.join(WEBAPP_DIR, rel))
        # cegah path traversal keluar dari WEBAPP_DIR
        if not full.startswith(WEBAPP_DIR + os.sep) and full != WEBAPP_DIR:
            return self._json({"error": "not found"}, 404)
        if not os.path.isfile(full):
            # SPA fallback ke index.html
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
