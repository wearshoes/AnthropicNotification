#!/usr/bin/env bash
# TDD Guard Hook: Runs before writing to src/ files.
# Checks that a corresponding test file exists in tests/.
# If not, blocks the write with exit code 2.

set -euo pipefail

INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | python -c "
import sys, json
data = json.load(sys.stdin)
tool_input = data.get('tool_input', {})
print(tool_input.get('file_path', '') or tool_input.get('file_path', ''))
" 2>/dev/null || echo "")

# Normalize path separators
FILE_PATH=$(echo "$FILE_PATH" | sed 's|\\|/|g')

# Only guard src/**/*.py files (not __init__.py, not _template files)
if [[ ! "$FILE_PATH" =~ src/.*\.py$ ]] || [[ "$FILE_PATH" =~ __init__\.py$ ]]; then
    exit 0
fi

# Skip files starting with _ (templates, internal utilities)
BASENAME=$(basename "$FILE_PATH")
if [[ "$BASENAME" == _* ]]; then
    exit 0
fi

# Derive expected test file path
# src/scraper.py -> tests/test_scraper.py
# src/formatters/wechat_work.py -> tests/formatters/test_wechat_work.py
REL_PATH="${FILE_PATH#*/src/}"
if [[ "$FILE_PATH" == src/* ]]; then
    REL_PATH="${FILE_PATH#src/}"
fi

DIR_PART=$(dirname "$REL_PATH")
FILE_PART=$(basename "$REL_PATH")
TEST_FILE_PART="test_${FILE_PART}"

if [[ "$DIR_PART" == "." ]]; then
    TEST_PATH="tests/${TEST_FILE_PART}"
else
    TEST_PATH="tests/${DIR_PART}/${TEST_FILE_PART}"
fi

PROJECT_DIR="${CODEBUDDY_PROJECT_DIR:-$(pwd)}"
# Normalize PROJECT_DIR path separators
PROJECT_DIR=$(echo "$PROJECT_DIR" | sed 's|\\|/|g')
FULL_TEST_PATH="${PROJECT_DIR}/${TEST_PATH}"

if [[ ! -f "$FULL_TEST_PATH" ]]; then
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"[TDD Guard] Test file '${TEST_PATH}' does not exist. Write the test FIRST before implementing '${FILE_PATH}'. This is the TDD RED step.\"}}"
    exit 2
fi

exit 0
