---
name: category-add
description: Add a new monitored category to the Anthropic website monitor. Guides through OpenSpec + TDD workflow to update sitemap.py, tests, and docs.
license: MIT
metadata:
  author: project
  version: "1.0"
---

Add a new monitored URL category with full OpenSpec + TDD workflow.

**Input**: Category name and URL path prefix (e.g., `blog /blog/`).

If no input provided, ask the user for both name and path.

---

## Step 1: Derive Names

From the input, derive:

```
Category: blog
├── Path prefix:   /blog/
├── CATEGORIES entry: "blog": "/blog/"
├── Code file:     src/sitemap.py (modify CATEGORIES dict)
├── Test file:     tests/test_sitemap.py (add category test cases)
├── Change name:   add-blog-category
└── Docs:          README.md, README_EN.md, CODEBUDDY.md
```

Announce to user before proceeding.

---

## Step 2: Create OpenSpec Change

```bash
openspec new change "add-{name}-category"
```

Create artifacts:

### proposal.md
- Why: Monitor {name} content on Anthropic website
- What: Add `"{name}": "/{path}/"` to CATEGORIES, update tests + docs

### specs/{name}-category/spec.md
- Requirement: Filter URLs with path prefix `/{path}/`
- Scenarios: matching URLs, non-matching, index page excluded

### design.md
- Simple: add one entry to CATEGORIES dict
- Tests: add category to existing test fixtures

### tasks.md (TDD order)
```
## 1. Tests
- [ ] 1.1 Update tests/test_sitemap.py: add {name} to test fixtures

## 2. Implementation
- [ ] 2.1 Add "{name}": "/{path}/" to CATEGORIES in src/sitemap.py

## 3. Documentation
- [ ] 3.1 Update README.md monitored pages table
- [ ] 3.2 Update README_EN.md monitored pages table
- [ ] 3.3 Update CODEBUDDY.md if needed

## 4. Verify
- [ ] 4.1 Run full test suite

## 5. Ship
- [ ] 5.1 Commit, push, sync specs, archive change
```

---

## Step 3: TDD Implementation

### RED — Update tests first

Read `tests/test_sitemap.py` and update:
- `test_filters_known_categories`: add the new category to test data and assertions
- `test_excludes_non_matching_urls`: verify new category shows up with empty set when no matching URLs
- Add a specific test for the new category if needed

Run tests, confirm the new assertions FAIL:
```bash
python -m pytest tests/test_sitemap.py -v
```

### GREEN — Add CATEGORIES entry

Read `src/sitemap.py` and add to the CATEGORIES dict:
```python
CATEGORIES = {
    ...
    "{name}": "/{path}/",
}
```

Run tests, confirm GREEN:
```bash
python -m pytest tests/test_sitemap.py -v
```

---

## Step 4: Update Documentation

### README.md
Add row to the monitored pages table:
```
| {name} | `/{path}/*` | {description} |
```

### README_EN.md
Same table update in English.

### CODEBUDDY.md
Only if the architecture section references monitored categories.

---

## Step 5: Verify

```bash
python -m pytest tests/ -v
```

---

## Step 6: Ship

1. Mark all tasks complete
2. `git add -A && git commit -m "feat: add {name} category monitoring"`
3. `git push`
4. Sync specs + archive the change
5. Commit + push the archive

---

## Guardrails

- ALWAYS update tests BEFORE modifying CATEGORIES (TDD)
- ALWAYS update both README files (Chinese + English)
- NEVER remove existing categories
- The path prefix MUST end with `/` (e.g., `/blog/` not `/blog`)
- Run full test suite before shipping
