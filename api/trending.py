from __future__ import annotations

# ruff: noqa: E402, INP001
import json
import sys
import time
from datetime import datetime, timezone
from functools import partial
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import ytmusicapi.ytmusic as ytmusic_module
from ytmusicapi import YTMusic
from ytmusicapi.constants import SUPPORTED_LOCATIONS

ytmusic_module.get_visitor_id = lambda request_func: {"X-Goog-Visitor-Id": ""}

CACHE_TTL_SECONDS = 60
_CACHE: dict[tuple[str, int], tuple[float, dict]] = {}

COUNTRY_LABELS = {
    "": "Global",
    "GLOBAL": "Global",
    "ZZ": "Global",
    "IN": "India",
    "US": "United States",
    "GB": "United Kingdom",
    "JP": "Japan",
    "KR": "South Korea",
    "BR": "Brazil",
    "DE": "Germany",
}


def _normalize_country(raw_country: str | None) -> str:
    country = (raw_country or "IN").strip().upper()
    if country in {"GLOBAL", "ZZ", ""}:
        return ""
    if country not in SUPPORTED_LOCATIONS:
        raise ValueError(f"Unsupported country code: {country}")
    return country


def _parse_limit(raw_limit: str | None) -> int:
    if not raw_limit:
        return 20

    try:
        limit = int(raw_limit)
    except ValueError as exc:
        raise ValueError("limit must be a number") from exc

    if limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50")

    return limit


def _artists_text(item: dict) -> str:
    return ", ".join(artist.get("name", "") for artist in item.get("artists", []) if artist.get("name"))


def _normalize_song(item: dict, rank: int) -> dict:
    video_id = item.get("videoId")

    return {
        "rank": rank,
        "title": item.get("title", "Untitled"),
        "videoId": video_id,
        "videoType": item.get("videoType"),
        "artists": item.get("artists", []),
        "artistsText": _artists_text(item),
        "playlistId": item.get("playlistId"),
        "thumbnails": item.get("thumbnails", []),
        "isExplicit": bool(item.get("isExplicit", False)),
        "views": item.get("views"),
        "youtubeMusicUrl": f"https://music.youtube.com/watch?v={video_id}" if video_id else None,
        "youtubeUrl": f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
    }


def _load_trending(country: str, limit: int) -> dict:
    cache_key = (country, limit)
    cached = _CACHE.get(cache_key)
    if cached and (time.monotonic() - cached[0]) < CACHE_TTL_SECONDS:
        payload = cached[1].copy()
        payload["cached"] = True
        return payload

    session = requests.Session()
    session.request = partial(session.request, timeout=20)

    ytmusic = YTMusic(location=country, requests_session=session)
    trending = ytmusic.get_trending_songs(limit=limit)
    items = [_normalize_song(item, index) for index, item in enumerate(trending.get("items", []), start=1)]
    country_key = country or "GLOBAL"

    payload = {
        "ok": True,
        "cached": False,
        "source": "ytmusicapi.get_trending_songs",
        "country": country_key,
        "countryLabel": COUNTRY_LABELS.get(country_key, country_key),
        "playlist": trending.get("playlist"),
        "count": len(items),
        "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "items": items,
    }
    _CACHE[cache_key] = (time.monotonic(), payload)
    return payload


class handler(BaseHTTPRequestHandler):
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
        self._send_json(204, {})

    def do_GET(self) -> None:
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
