#!/usr/bin/env bash
# CI Status Hook: After git push, query GitHub Actions for latest run status.
# Best-effort: requires GITHUB_TOKEN, skips silently if unavailable.

set -uo pipefail

INPUT=$(cat)

# Extract the bash command from tool_input
COMMAND=$(echo "$INPUT" | python -c "
import sys, json
data = json.load(sys.stdin)
tool_input = data.get('tool_input', {})
print(tool_input.get('command', ''))
" 2>/dev/null || echo "")

# Only trigger on git push commands
if [[ ! "$COMMAND" =~ git\ push ]] && [[ ! "$COMMAND" =~ git\ push ]]; then
    exit 0
fi

# Need GITHUB_TOKEN to query API
if [[ -z "${GITHUB_TOKEN:-}" ]]; then
    exit 0
fi

# Extract repo info from git remote
PROJECT_DIR="${CODEBUDDY_PROJECT_DIR:-$(pwd)}"
PROJECT_DIR=$(echo "$PROJECT_DIR" | sed 's|\\|/|g')
REMOTE_URL=$(cd "$PROJECT_DIR" && git remote get-url origin 2>/dev/null || echo "")

if [[ -z "$REMOTE_URL" ]]; then
    exit 0
fi

# Extract owner/repo from remote URL
REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]([^/]+/[^/.]+)(\.git)?$|\1|')

if [[ -z "$REPO" ]] || [[ "$REPO" == "$REMOTE_URL" ]]; then
    exit 0
fi

# Wait a few seconds for GitHub to register the push
sleep 5

# Query latest run
RESULT=$(python -c "
import os, urllib.request, json
token = os.environ.get('GITHUB_TOKEN', '')
repo = '$REPO'
try:
    req = urllib.request.Request(f'https://api.github.com/repos/{repo}/actions/runs?per_page=1')
    req.add_header('Authorization', f'token {token}')
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    runs = data.get('workflow_runs', [])
    if runs:
        r = runs[0]
        status = r.get('status', 'unknown')
        conclusion = r.get('conclusion') or 'pending'
        name = r.get('name', '')
        run_id = r.get('id', '')
        html_url = r.get('html_url', '')
        print(f'[CI] {name} #{run_id}: status={status}, conclusion={conclusion}')
        print(f'     {html_url}')
    else:
        print('[CI] No workflow runs found')
except Exception as e:
    print(f'[CI] Failed to query Actions: {e}')
" 2>/dev/null || echo "[CI] Query failed")

echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PostToolUse\",\"additionalContext\":\"$RESULT\"}}"
exit 0
