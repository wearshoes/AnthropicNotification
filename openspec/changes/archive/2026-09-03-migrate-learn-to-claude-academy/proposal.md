## Why

Anthropic retired the `/learn/*` pages from its primary sitemap and redirects them to Claude Academy. The snapshot guard now correctly rejects an empty `learn` category, but that blocks every category and has left scheduled production runs failing since 2026-09-01.

## What Changes

- Fetch both the Anthropic and Claude Academy sitemaps as one fail-closed snapshot.
- Route the `learn` category to collection landing pages on the exact `https://academy.claude.com` origin.
- Keep strict exact-origin validation for sitemap entries, redirects, and metadata enrichment.
- Update the workflow's immutable action pins to maintained Node 24-compatible releases.
- Migrate the learn baseline without replaying existing Academy content and remove stale duplicate baselines.

## Capabilities

### Modified Capabilities
- `sitemap-parser`: Add Claude Academy as a trusted, category-scoped sitemap source.
- `ci-workflow`: Refresh immutable third-party action references without changing scheduling.

## Impact

- Changes to `src/sitemap.py`, `src/main.py`, sitemap/enrichment tests, workflow pins, documentation, and specifications.
- One-time verified GitHub Issue migration for baseline state.
