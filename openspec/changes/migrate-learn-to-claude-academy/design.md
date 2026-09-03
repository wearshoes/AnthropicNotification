## Context

The three historical Anthropic Learn URLs now redirect to matching collection pages on `academy.claude.com`. Claude Academy publishes 767 sitemap URLs, including individual lessons. Monitoring all of them would change the category's meaning, replay a large historical backlog, and quickly pressure the GitHub Issue baseline body limit.

## Decisions

### 1. Preserve learn category semantics

Only exact-origin Claude Academy `/collections/*` landing pages enter `learn`. Individual courses, lessons, tutorials, product pages, indexes, and unrelated paths remain excluded.

### 2. Fetch both sources fail closed

The production snapshot combines `www.anthropic.com/sitemap.xml` and `academy.claude.com/sitemap.xml`. A fetch or parse failure from either source fails the run after pending delivery has been attempted.

### 3. Use route-specific exact origins

Each category declares both an exact host and a path prefix. Trusting the Academy host does not allow its URLs into news, research, or engineering, and lookalike hosts remain rejected.

### 4. Seed migrated content before deployment

Before code deployment, union the current Academy collection URLs into the newest learn baseline and verify the write. Historical Anthropic Learn URLs remain in the monotonic baseline. This prevents current Academy collections from being emitted as new notifications.

### 5. Keep scheduling unchanged

The 30-minute best-effort cron remains unchanged. Only action implementation pins move to maintained releases and remain fixed to full commit SHAs.

## Risks / Trade-offs

- Academy can change its sitemap or collection URL scheme again; the existing completeness guard will fail closed.
- Monitoring collections intentionally does not announce every Academy lesson.
- A collection added between baseline migration and deployment is treated as a legitimate new item.
