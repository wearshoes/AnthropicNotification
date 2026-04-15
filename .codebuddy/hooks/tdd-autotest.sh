#!/usr/bin/env bash
# TDD Post-Write Hook: After writing/editing src/ files, run related tests.
# Reports test results back to the agent as additional context.

set -uo pipefail

INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | python -c "
import sys, json
data = json.load(sys.stdin)
tool_input = data.get('tool_input', {})
print(tool_input.get('file_path', '') or tool_input.get('file_path', ''))
" 2>/dev/null || echo "")

# Normalize path separators
FILE_PATH=$(echo "$FILE_PATH" | sed 's|\\|/|g')

# Only run for src/**/*.py files (not __init__.py)
if [[ ! "$FILE_PATH" =~ src/.*\.py$ ]] || [[ "$FILE_PATH" =~ __init__\.py$ ]]; then
    exit 0
fi

# Derive test file path
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
PROJECT_DIR=$(echo "$PROJECT_DIR" | sed 's|\\|/|g')
FULL_TEST_PATH="${PROJECT_DIR}/${TEST_PATH}"

if [[ ! -f "$FULL_TEST_PATH" ]]; then
    exit 0
fi

# Run the specific test file
cd "$PROJECT_DIR"
TEST_OUTPUT=$(python -m pytest "$TEST_PATH" -v --tb=short 2>&1) || true
EXIT_CODE=${PIPESTATUS[0]:-$?}

PASSED=$(echo "$TEST_OUTPUT" | grep -oP '\d+ passed' | grep -oP '\d+' || echo "0")
FAILED=$(echo "$TEST_OUTPUT" | grep -oP '\d+ failed' | grep -oP '\d+' || echo "0")

if [[ "$EXIT_CODE" -eq 0 ]]; then
    STATUS="GREEN (all passing)"
else
    STATUS="RED (${FAILED} failing)"
fi

echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PostToolUse\",\"additionalContext\":\"[TDD Auto-Test] ${TEST_PATH}: ${STATUS} — ${PASSED} passed, ${FAILED} failed\"}}"
exit 0
