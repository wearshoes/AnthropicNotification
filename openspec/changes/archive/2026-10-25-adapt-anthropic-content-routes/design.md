## Context

The primary sitemap now exposes 278 news paths and 208 research paths but no engineering article paths. All 26 historical engineering URLs redirect to `/research/<same-slug>`. The engineering landing page remains authoritative for category membership and currently links to 24 article pages. Prefix-only routing can no longer preserve the four logical categories.

## Decisions

### 1. Treat the engineering landing page as a required source

The monitor fetches `/engineering` through the same bounded, exact-origin redirect validation used for sitemaps. An unavailable or empty engineering source fails closed through the existing snapshot completeness guard.

### 2. Accept only sitemap-backed article links

Engineering candidates must canonicalize to the exact Anthropic origin, use a single `/research/<slug>` segment, and also exist in the fetched sitemap. Navigation, research team, lookalike-host, nested, and stale links are ignored.

### 3. Assign every current URL to at most one category

Engineering landing-page membership overrides the generic research prefix. The selected URLs are removed from research before being added to engineering.

### 4. Exclude structural pages

Exact news section landing paths are excluded. Research accepts only one path segment after `/research/`, excluding `/research/team/*`. Direct legacy `/engineering/<slug>` sitemap entries remain supported for backward compatibility.

### 5. Perform a controlled monotonic migration

Before deployment, union canonical replacements for moved engineering URLs and historical pages newly surfaced by the taxonomy change into their target baselines. Do not seed content first published after the last successful run at 2026-10-20T15:28:26Z. Those items must flow through the durable outbox after deployment.

## Risks / Trade-offs

- The engineering landing page is HTML rather than XML. Structural URL rules and sitemap intersection avoid dependence on generated CSS class names.
- Anthropic can redesign the landing page again. An empty result fails visibly instead of silently dropping a category.
- Exact news section exclusions require review if Anthropic adds another section landing page.
