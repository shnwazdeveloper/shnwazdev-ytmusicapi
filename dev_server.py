from __future__ import annotations

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ytmusic_endpoint import execute_endpoint, json_default

ROOT_API_ENDPOINTS = {"new_releases", "music_premium/musicfeed"}


class DevHandler(SimpleHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=json_default).encode("utf-8")
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
        parsed_url = urlparse(self.path)
        if parsed_url.path.startswith("/api/") or parsed_url.path.strip("/") in ROOT_API_ENDPOINTS:
            self._send_json(204, {})
            return

        super().do_OPTIONS()

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        root_endpoint = parsed_url.path.strip("/")
        if parsed_url.path.startswith("/api/") or root_endpoint in ROOT_API_ENDPOINTS:
            query = parse_qs(parsed_url.query)
            if root_endpoint in ROOT_API_ENDPOINTS:
                endpoint = root_endpoint
            else:
                endpoint = parsed_url.path.removeprefix("/api/").strip("/") or "ytmusic"
                if endpoint == "ytmusic":
                    endpoint = query.get("method", query.get("endpoint", ["ytmusic"]))[0]

            try:
                self._send_json(200, execute_endpoint(endpoint, query))
            except ValueError as exc:
                self._send_json(400, {"ok": False, "endpoint": endpoint, "error": str(exc)})
            except Exception as exc:
                self._send_json(
                    502,
                    {
                        "ok": False,
                        "endpoint": endpoint,
                        "error": "Unable to load YouTube Music data right now.",
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
