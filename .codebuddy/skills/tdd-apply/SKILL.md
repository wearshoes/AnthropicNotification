---
name: tdd-apply
description: TDD-driven implementation skill. Enforces RED-GREEN-REFACTOR cycle for every task. Use this instead of direct coding when implementing features.
license: MIT
metadata:
  author: project
  version: "1.0"
---

Implement tasks using strict Test-Driven Development (RED → GREEN → REFACTOR).

**Input**: A description of what to implement, or an OpenSpec change name to work from.

---

## Core Rule

**You MUST NOT write any implementation code in `src/` before its corresponding test exists in `tests/` and has been run to confirm failure (RED).**

This is non-negotiable. If you catch yourself writing implementation first, stop, delete it, and start with the test.

---

## TDD Cycle

For each unit of work (function, class, module), follow this exact sequence:

### Step 1: RED — Write a Failing Test

1. Create or update the test file in `tests/` matching the module path:
   - `src/scraper.py` → `tests/test_scraper.py`
   - `src/differ.py` → `tests/test_differ.py`
   - `src/formatters/wechat_work.py` → `tests/formatters/test_wechat_work.py`

2. Write test(s) that define the expected behavior. Tests should:
   - Cover the happy path
   - Cover edge cases (empty input, missing data, errors)
   - Use `pytest` style (plain functions, not unittest classes)
   - Mock external dependencies (HTTP requests, file I/O) with `unittest.mock` or `pytest-mock`

3. Run the tests and **confirm they FAIL**:
   ```bash
   python -m pytest tests/test_<module>.py -v
   ```

4. Report the RED status:
   ```
   [TDD] module=<name> step=RED tests_written=<N> status=FAILING ✓
   ```

### Step 2: GREEN — Write Minimal Implementation

1. Write the **minimum code** in `src/` to make the failing tests pass. No more, no less.

2. Run the tests and **confirm they PASS**:
   ```bash
   python -m pytest tests/test_<module>.py -v
   ```

3. If any test fails, fix the implementation (not the test, unless the test has a bug).

4. Report the GREEN status:
   ```
   [TDD] module=<name> step=GREEN tests=<passed>/<total> status=ALL PASSING ✓
   ```

### Step 3: REFACTOR (Optional)

1. If the code can be improved (duplication, naming, structure), refactor now.
2. Run all tests again to confirm nothing broke:
   ```bash
   python -m pytest tests/ -v
   ```
3. Report:
   ```
   [TDD] module=<name> step=REFACTOR tests=<passed>/<total> status=ALL PASSING ✓
   ```

---

## Working With OpenSpec Changes

When implementing an OpenSpec change:

1. Get the change context:
   ```bash
   openspec instructions apply --change "<name>" --json
   ```
2. Read all context files (proposal, design, tasks)
3. For each task in `tasks.md`, apply the TDD cycle above
4. Mark task complete only AFTER GREEN: `- [ ]` → `- [x]`
5. **Never mark a task complete if tests are failing**

---

## Working in a Team

When spawned as a teammate:

1. After completing each TDD cycle, report via SendMessage:
   ```
   [TDD] module=<name> step=GREEN tests=<N>/<N> passed
   Files: tests/test_<name>.py, src/<name>.py
   ```

2. If you discover an issue that affects other teammates' work, notify them immediately via SendMessage.

3. Before starting, check TaskList for available tasks and claim one with TaskUpdate.

4. After GREEN, mark your task as completed and check TaskList for the next available task.

---

## Test File Conventions

```python
# tests/test_scraper.py
"""Tests for src/scraper.py — written BEFORE implementation."""

import pytest
from unittest.mock import patch, MagicMock

# Test naming: test_<function>_<scenario>_<expected>
def test_news_scraper_parse_extracts_articles():
    ...

def test_news_scraper_parse_empty_page_returns_empty_list():
    ...

def test_base_scraper_fetch_retries_on_timeout():
    ...
```

---

## Guardrails

- **NEVER** write `src/` code before `tests/` code for that module
- **NEVER** mark a task complete with failing tests
- **ALWAYS** run pytest after writing tests (confirm RED) and after writing implementation (confirm GREEN)
- **ALWAYS** run the full test suite before declaring a module done
- If a test is hard to write, that's a design signal — simplify the interface
- Mock external dependencies (network, filesystem), never hit real APIs in tests
- Keep tests fast — no sleeps, no real network calls
