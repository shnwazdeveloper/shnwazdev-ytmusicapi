from __future__ import annotations

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from api.trending import _load_trending, _normalize_country, _parse_limit


class DevHandler(SimpleHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        if self.path.startswith("/api/trending"):
            self._send_json(204, {})
            return

        super().do_OPTIONS()

    def do_GET(self) -> None:
        if self.path.startswith("/api/trending"):
            query = parse_qs(urlparse(self.path).query)

            try:
                country = _normalize_country(query.get("country", [None])[0])
                limit = _parse_limit(query.get("limit", [None])[0])
                self._send_json(200, _load_trending(country, limit))
            except ValueError as exc:
                self._send_json(400, {"ok": False, "error": str(exc)})
            except Exception as exc:
                self._send_json(
                    502,
                    {
                        "ok": False,
                        "error": "Unable to load YouTube Music trending songs right now.",
                        "details": str(exc),
                    },
                )
            return

        super().do_GET()


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    server = ThreadingHTTPServer(("127.0.0.1", 3000), lambda *args, **kwargs: DevHandler(*args, directory=root, **kwargs))
    print("Local dev server ready at http://127.0.0.1:3000")
    server.serve_forever()
