from __future__ import annotations

import json
import time
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from functools import partial
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

import requests

import ytmusicapi.ytmusic as ytmusic_module
from ytmusicapi import YTMusic
from ytmusicapi.constants import SUPPORTED_LOCATIONS
from ytmusicapi.exceptions import YTMusicError, YTMusicUserError

ytmusic_module.get_visitor_id = lambda request_func: {"X-Goog-Visitor-Id": ""}

CACHE_TTL_SECONDS = 60
_CACHE: dict[tuple[str, tuple[tuple[str, str], ...]], tuple[float, dict]] = {}

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

ENDPOINTS = [
    {
        "name": "trending",
        "path": "/api/trending",
        "params": "country",
        "description": "Current country trending songs. Unlimited by default.",
        "example": "/api/trending?country=IN",
    },
    {
        "name": "search",
        "path": "/api/search",
        "params": "q, filter, scope",
        "description": "Search YouTube Music. Filtered searches fetch all continuation pages by default.",
        "example": "/api/search?q=arijit%20singh&filter=songs",
    },
    {
        "name": "suggestions",
        "path": "/api/suggestions",
        "params": "q, detailed",
        "description": "Search suggestions.",
        "example": "/api/suggestions?q=alone",
    },
    {
        "name": "charts",
        "path": "/api/charts",
        "params": "country",
        "description": "YouTube Music chart playlists and artists for a country.",
        "example": "/api/charts?country=IN",
    },
    {
        "name": "new_releases",
        "path": "/api/new_releases",
        "params": "limit",
        "description": "Latest album, EP, and single releases from YouTube Music. Unlimited by default.",
        "example": "/api/new_releases",
    },
    {
        "name": "playlist",
        "path": "/api/playlist",
        "params": "id",
        "description": "Playlist metadata and all tracks.",
        "example": "/api/playlist?id=OLAK5uy_lSTp1DIuzZBUyee3kDsXwPgP25WdfwB40",
    },
    {
        "name": "song",
        "path": "/api/song",
        "params": "id",
        "description": "Song or video metadata.",
        "example": "/api/song?id=0KYJPoGJcMc",
    },
    {
        "name": "song_related",
        "path": "/api/song_related",
        "params": "id",
        "description": "Related music sections from a song related browse id.",
        "example": "/api/song_related?id=MPRE...",
    },
    {
        "name": "album",
        "path": "/api/album",
        "params": "id",
        "description": "Album metadata and tracks.",
        "example": "/api/album?id=MPREb_...",
    },
    {
        "name": "album_browse_id",
        "path": "/api/album_browse_id",
        "params": "id",
        "description": "Resolve an album browse id from an audio playlist id.",
        "example": "/api/album_browse_id?id=OLAK5uy_...",
    },
    {
        "name": "artist",
        "path": "/api/artist",
        "params": "id",
        "description": "Artist overview.",
        "example": "/api/artist?id=UCDxKh1gFWeYsqePvgVzmPoQ",
    },
    {
        "name": "artist_albums",
        "path": "/api/artist_albums",
        "params": "id, params",
        "description": "All artist albums from a params token returned by the artist endpoint.",
        "example": "/api/artist_albums?id=UC...&params=...",
    },
    {
        "name": "lyrics",
        "path": "/api/lyrics",
        "params": "id, timestamps",
        "description": "Lyrics from a lyrics browse id.",
        "example": "/api/lyrics?id=MPLYt_...",
    },
    {
        "name": "moods",
        "path": "/api/moods",
        "params": "",
        "description": "Mood and genre categories.",
        "example": "/api/moods",
    },
    {
        "name": "mood_playlists",
        "path": "/api/mood_playlists",
        "params": "params",
        "description": "All playlists for a mood or genre params token.",
        "example": "/api/mood_playlists?params=ggM...",
    },
    {
        "name": "explore",
        "path": "/api/explore",
        "params": "",
        "description": "Raw YouTube Music explore feed.",
        "example": "/api/explore",
    },
    {
        "name": "ytmusic",
        "path": "/api/ytmusic",
        "params": "method",
        "description": "Generic dispatcher for the endpoint names above.",
        "example": "/api/ytmusic?method=search&q=arijit%20singh&filter=songs",
    },
]


def _first(query: dict[str, list[str]], key: str, default: str | None = None) -> str | None:
    value = query.get(key, [default])[0]
    if value is None:
        return default
    value = value.strip()
    return value if value else default


def _required(query: dict[str, list[str]], *keys: str) -> str:
    for key in keys:
        value = _first(query, key)
        if value:
            return value
    raise ValueError(f"Missing required parameter: {keys[0]}")


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_limit(value: str | None) -> int | None:
    if value is None or value.strip().lower() in {"", "all", "none", "null", "unlimited"}:
        return None

    try:
        limit = int(value)
    except ValueError as exc:
        raise ValueError("limit must be a positive number, all, none, or unlimited") from exc

    if limit < 1:
        raise ValueError("limit must be a positive number")

    return limit


def normalize_country(raw_country: str | None) -> str:
    country = (raw_country or "IN").strip().upper()
    if country in {"GLOBAL", "ZZ", ""}:
        return ""
    if country not in SUPPORTED_LOCATIONS:
        raise ValueError(f"Unsupported country code: {country}")
    return country


def _cache_key(endpoint: str, query: dict[str, list[str]]) -> tuple[str, tuple[tuple[str, str], ...]]:
    pairs = tuple(sorted((key, values[0] if values else "") for key, values in query.items() if key != "t"))
    return (endpoint, pairs)


def _make_ytmusic() -> YTMusic:
    session = requests.Session()
    session.request = partial(session.request, timeout=25)
    return YTMusic(requests_session=session)


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
        "album": item.get("album"),
        "duration": item.get("duration"),
        "duration_seconds": item.get("duration_seconds"),
        "playlistId": item.get("playlistId"),
        "thumbnails": item.get("thumbnails", []),
        "isExplicit": bool(item.get("isExplicit", False)),
        "views": item.get("views"),
        "youtubeMusicUrl": f"https://music.youtube.com/watch?v={video_id}" if video_id else None,
        "youtubeUrl": f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
    }


def _envelope(endpoint: str, data: object, extra: dict | None = None) -> dict:
    payload = {
        "ok": True,
        "endpoint": endpoint,
        "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "data": data,
    }
    if isinstance(data, list):
        payload["count"] = len(data)
    if extra:
        payload.update(extra)
    return payload


def _load_trending(query: dict[str, list[str]]) -> dict:
    country = normalize_country(_first(query, "country"))
    limit = parse_limit(_first(query, "limit"))
    cache_key = _cache_key("trending", query)
    cached = _CACHE.get(cache_key)
    if cached and (time.monotonic() - cached[0]) < CACHE_TTL_SECONDS:
        payload = cached[1].copy()
        payload["cached"] = True
        return payload

    trending = _make_ytmusic().get_trending_songs(country=country or "ZZ", limit=limit)
    items = [_normalize_song(item, index) for index, item in enumerate(trending.get("items", []), start=1)]
    country_key = country or "GLOBAL"
    payload = {
        "ok": True,
        "cached": False,
        "endpoint": "trending",
        "source": "ytmusicapi.get_trending_songs",
        "country": country_key,
        "countryLabel": COUNTRY_LABELS.get(country_key, country_key),
        "playlist": trending.get("playlist"),
        "playlistTitle": trending.get("title"),
        "count": len(items),
        "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "items": items,
    }
    _CACHE[cache_key] = (time.monotonic(), payload)
    return payload


def _load_new_releases(query: dict[str, list[str]]) -> dict:
    limit = parse_limit(_first(query, "limit"))
    cache_key = _cache_key("new_releases", query)
    cached = _CACHE.get(cache_key)
    if cached and (time.monotonic() - cached[0]) < CACHE_TTL_SECONDS:
        payload = cached[1].copy()
        payload["cached"] = True
        return payload

    releases = _make_ytmusic().get_explore().get("new_releases", [])
    if limit is not None:
        releases = releases[:limit]

    payload = _envelope(
        "new_releases",
        releases,
        {"cached": False, "source": "ytmusicapi.get_explore.new_releases"},
    )
    _CACHE[cache_key] = (time.monotonic(), payload)
    return payload


def execute_endpoint(endpoint: str, query: dict[str, list[str]]) -> dict:
    endpoint = endpoint.strip().lower().replace("-", "_")
    if endpoint == "trending":
        return _load_trending(query)
    if endpoint == "new_releases":
        return _load_new_releases(query)
    if endpoint == "endpoints":
        return _envelope("endpoints", ENDPOINTS)

    yt = _make_ytmusic()

    if endpoint == "search":
        data = yt.search(
            _required(query, "q", "query"),
            filter=_first(query, "filter"),
            scope=_first(query, "scope"),
            limit=parse_limit(_first(query, "limit")),
            ignore_spelling=parse_bool(_first(query, "ignore_spelling")),
        )
    elif endpoint == "suggestions":
        data = yt.get_search_suggestions(
            _required(query, "q", "query"),
            detailed_runs=parse_bool(_first(query, "detailed")),
        )
    elif endpoint == "charts":
        data = yt.get_charts(country=normalize_country(_first(query, "country")) or "ZZ")
    elif endpoint == "playlist":
        data = yt.get_playlist(_required(query, "id", "playlistId", "playlist"), limit=parse_limit(_first(query, "limit")))
    elif endpoint == "song":
        data = yt.get_song(_required(query, "id", "videoId", "video"))
    elif endpoint == "song_related":
        data = yt.get_song_related(_required(query, "id", "browseId"))
    elif endpoint == "album":
        data = yt.get_album(_required(query, "id", "browseId", "albumId"))
    elif endpoint == "album_browse_id":
        data = yt.get_album_browse_id(_required(query, "id", "audioPlaylistId", "playlistId"))
    elif endpoint == "artist":
        data = yt.get_artist(_required(query, "id", "channelId", "artistId"))
    elif endpoint == "artist_albums":
        data = yt.get_artist_albums(
            _required(query, "id", "channelId", "artistId"),
            _required(query, "params"),
            limit=parse_limit(_first(query, "limit")),
        )
    elif endpoint == "lyrics":
        data = yt.get_lyrics(_required(query, "id", "browseId"), timestamps=parse_bool(_first(query, "timestamps")))
    elif endpoint == "moods":
        data = yt.get_mood_categories()
    elif endpoint == "mood_playlists":
        data = yt.get_mood_playlists(_required(query, "params"))
    elif endpoint == "explore":
        data = yt.get_explore()
    else:
        raise ValueError(f"Unknown endpoint: {endpoint}")

    return _envelope(endpoint, data)


def json_default(value: object) -> object:
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "__dict__"):
        return value.__dict__
    return str(value)


class EndpointHandler(BaseHTTPRequestHandler):
    endpoint = ""

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
        self._send_json(204, {})

    def do_GET(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        endpoint = self.endpoint or _required(query, "method", "endpoint")

        try:
            self._send_json(200, execute_endpoint(endpoint, query))
        except (ValueError, YTMusicUserError) as exc:
            self._send_json(400, {"ok": False, "endpoint": endpoint, "error": str(exc)})
        except (requests.RequestException, YTMusicError) as exc:
            self._send_json(502, {"ok": False, "endpoint": endpoint, "error": str(exc)})
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
