#!/usr/bin/env bash
# OpenSpec Guard Hook: Checks for active OpenSpec change before src/ modifications.
# Uses "ask" mode (soft constraint) — prompts confirmation, does not hard block.

set -uo pipefail

INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | python -c "
import sys, json
data = json.load(sys.stdin)
tool_input = data.get('tool_input', {})
print(tool_input.get('file_path', '') or '')
" 2>/dev/null || echo "")

FILE_PATH=$(echo "$FILE_PATH" | sed 's|\\|/|g')

# Only guard src/**/*.py files (not __init__.py, not _ prefixed)
if [[ ! "$FILE_PATH" =~ src/.*\.py$ ]] || [[ "$FILE_PATH" =~ __init__\.py$ ]]; then
    exit 0
fi
BASENAME=$(basename "$FILE_PATH")
if [[ "$BASENAME" == _* ]]; then
    exit 0
fi

# Check for active OpenSpec changes
OPENSPEC_DIR="${CODEBUDDY_PROJECT_DIR:-$(pwd)}"
OPENSPEC_DIR=$(echo "$OPENSPEC_DIR" | sed 's|\\|/|g')
CHANGES_DIR="$OPENSPEC_DIR/openspec/changes"

if [[ ! -d "$CHANGES_DIR" ]]; then
    exit 0
fi

# Count non-archive directories in changes/
ACTIVE_CHANGES=0
for dir in "$CHANGES_DIR"/*/; do
    dir_name=$(basename "$dir")
    if [[ "$dir_name" != "archive" ]] && [[ -f "$dir/.openspec.yaml" ]]; then
        ACTIVE_CHANGES=$((ACTIVE_CHANGES + 1))
    fi
done

if [[ "$ACTIVE_CHANGES" -eq 0 ]]; then
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"ask\",\"permissionDecisionReason\":\"[OpenSpec Guard] No active OpenSpec change found. Consider running /opsx:propose before modifying src/ files. This ensures changes are tracked and documented.\"}}"
    exit 0
fi

exit 0
