shnwazdev-ytmusicapi
####################

Realtime YouTube Music trending songs API and light glass website by
`shnwazdeveloper <https://github.com/shnwazdeveloper>`__.

Live links
----------

* Website: https://shnwazdev-ytmusicapi.vercel.app/
* API docs: https://shnwazdev-ytmusicapi.vercel.app/docs.html
* Repository: https://github.com/shnwazdeveloper/shnwazdev-ytmusicapi

About
-----

``shnwazdev-ytmusicapi`` is a maintained fork of
`sigma67/ytmusicapi <https://github.com/sigma67/ytmusicapi>`__ with a Vercel-ready
website and public JSON endpoints for realtime YouTube Music data.

The project keeps the original Python ``ytmusicapi`` library behavior, then adds
the shnwazdev API layer, uncapped endpoint defaults, realtime trending songs, and
a clean light glass UI.

What this fork adds
-------------------

* Realtime YouTube Music trending songs endpoint.
* New releases endpoint for latest albums, EPs, and singles.
* Free public ``/music_premium/musicfeed`` endpoint for YouTube Music feed rows.
* Light theme landing page with glass-effect CSS and UI motion.
* Public API docs page.
* Single Vercel function dispatcher for all friendly API routes.
* No app-level default item cap on search, trending, playlist, and artist-album routes.
* GitHub docs and policies maintained for the shnwazdeveloper repo.

Public API
----------

All routes return JSON. Successful responses include ``ok``, ``endpoint``, and
``updatedAt``.

.. code-block:: text

    GET /api/trending?country=IN
    GET /api/search?q=arijit%20singh&filter=songs
    GET /api/suggestions?q=alone
    GET /api/charts?country=IN
    GET /api/new_releases
    GET /new_releases
    GET /api/music_premium/musicfeed
    GET /music_premium/musicfeed
    GET /api/playlist?id=PLAYLIST_ID
    GET /api/song?id=VIDEO_ID
    GET /api/song_related?id=BROWSE_ID
    GET /api/album?id=BROWSE_ID
    GET /api/album_browse_id?id=AUDIO_PLAYLIST_ID
    GET /api/artist?id=CHANNEL_ID
    GET /api/artist_albums?id=CHANNEL_ID&params=PARAMS_TOKEN
    GET /api/lyrics?id=LYRICS_BROWSE_ID
    GET /api/moods
    GET /api/mood_playlists?params=PARAMS_TOKEN
    GET /api/explore
    GET /api/endpoints
    GET /api/ytmusic?method=search&q=arijit%20singh&filter=songs

Limits
------

This fork removes the app-level default item cap for the public API routes where
the underlying YouTube Music continuation data is available. You can still pass
``limit=NUMBER`` when you intentionally want a smaller response.

Very large requests are still bounded by YouTube Music availability, network
conditions, and the Vercel function execution window.

Local development
-----------------

Install dependencies and run the local website/API server:

.. code-block:: powershell

    .\.venv\Scripts\python.exe -m pip install -e .
    .\.venv\Scripts\python.exe dev_server.py

Then open:

.. code-block:: text

    http://127.0.0.1:3000/
    http://127.0.0.1:3000/docs.html

Useful checks:

.. code-block:: powershell

    node --check app.js
    .\.venv\Scripts\python.exe -m ruff check ytmusic_endpoint.py dev_server.py api
    .\.venv\Scripts\python.exe -m pytest tests\mixins\test_explore.py -k get_trending_songs -q

Repository resources
--------------------

* `Contributing <CONTRIBUTING.rst>`__
* `Security policy <SECURITY.md>`__
* `MIT license <LICENSE>`__

Credits
-------

The core Python library is based on the excellent open source
`ytmusicapi <https://github.com/sigma67/ytmusicapi>`__ project. The realtime API,
Vercel website, endpoint docs, and light landing page are maintained in this fork
by `shnwazdeveloper <https://github.com/shnwazdeveloper>`__.
