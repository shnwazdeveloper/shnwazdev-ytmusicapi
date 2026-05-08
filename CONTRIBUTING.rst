Contributing to shnwazdev-ytmusicapi
####################################

Thanks for helping improve ``shnwazdev-ytmusicapi``. This repository is maintained
by `shnwazdeveloper <https://github.com/shnwazdeveloper>`__ and focuses on the
realtime YouTube Music API, Vercel website, endpoint docs, and the forked
``ytmusicapi`` library behavior used by those endpoints.

Good contributions
------------------

* Fix bugs in public API routes.
* Improve realtime trending, search, playlist, artist, album, mood, or lyrics endpoints.
* Improve the light glass website UI without adding dark-theme styling.
* Add clear docs and examples for endpoint usage.
* Add tests for changed library or endpoint behavior.

Issues
------

When opening an issue, include:

* The route or page affected.
* The request URL, with private tokens removed.
* Expected result and actual result.
* Screenshots for UI problems.
* Any console, Vercel, or Python error message that helps reproduce the issue.

Security problems should not be reported in public issues. Use the security
policy instead.

Local setup
-----------

From the repository root:

.. code-block:: powershell

    .\.venv\Scripts\python.exe -m pip install -e .
    .\.venv\Scripts\python.exe dev_server.py

Open the local app at:

.. code-block:: text

    http://127.0.0.1:3000/

Checks before a pull request
----------------------------

Run the focused checks that match your change:

.. code-block:: powershell

    node --check app.js
    .\.venv\Scripts\python.exe -m ruff check ytmusic_endpoint.py dev_server.py api
    .\.venv\Scripts\python.exe -m pytest tests\mixins\test_explore.py -k get_trending_songs -q

Pull request checklist
----------------------

* Keep changes focused.
* Do not remove upstream credit for ``sigma67/ytmusicapi``.
* Keep the website light themed.
* Do not add default item limits to public endpoints.
* Update ``README.rst`` or ``docs.html`` when endpoint behavior changes.
* Explain what you tested.

Upstream library work
---------------------

For changes that belong in the original library rather than this fork's website
or public endpoint layer, compare behavior with
`sigma67/ytmusicapi <https://github.com/sigma67/ytmusicapi>`__ and keep the fork
compatible where possible.
