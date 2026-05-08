# Security Policy

This security policy is for `shnwazdev-ytmusicapi`, maintained by
[`shnwazdeveloper`](https://github.com/shnwazdeveloper).

## Supported Versions

The `main` branch and the live Vercel deployment are supported.

## Reporting a Vulnerability

Please do not open a public issue for security problems.

Report vulnerabilities through GitHub Security Advisories:

https://github.com/shnwazdeveloper/shnwazdev-ytmusicapi/security/advisories/new

Include:

- Affected endpoint or page.
- Steps to reproduce.
- Expected impact.
- Any logs, screenshots, or request examples that are safe to share privately.

## Scope

In scope:

- Public API routes under `/api/*`.
- The Vercel-hosted website.
- Endpoint dispatcher behavior in `ytmusic_endpoint.py`.
- Client-side website code in `index.html`, `docs.html`, `styles.css`, and `app.js`.

Out of scope:

- Issues caused by YouTube Music availability or rate behavior.
- Vulnerabilities in user-owned deployments that modified this repository.

## Response

The maintainer will review valid reports, patch the project when needed, and
publish fixes through GitHub and Vercel.
