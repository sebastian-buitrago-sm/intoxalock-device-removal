#!/usr/bin/env bash
# build-pdf.sh — regenerate a styled solution-design PDF from its Markdown source.
#
# Usage:
#   build-pdf.sh <input.md> [output.pdf]
# If output.pdf is omitted, it is written next to the .md with the same basename.
#
# Reproduces the house style of Client-Handoff-original.pdf (see render.js) and
# prints with headless Chrome, the same engine the originals were made with.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IN="${1:?Usage: build-pdf.sh <input.md> [output.pdf]}"
OUT="${2:-${IN%.md}.pdf}"
[ -f "$IN" ] || { echo "ERROR: input not found: $IN" >&2; exit 1; }

# 1. Ensure `marked` is available (vendored in the skill dir).
if ! node -e "require('$SKILL_DIR/node_modules/marked')" 2>/dev/null; then
  echo "Installing marked@15 into skill dir..."
  ( cd "$SKILL_DIR" && npm install --no-save --silent marked@15 )
fi

# 2. Locate a Chrome/Chromium binary.
CHROME=""
for c in \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium" \
  "$(command -v google-chrome 2>/dev/null || true)" \
  "$(command -v chromium 2>/dev/null || true)" \
  "$(command -v chromium-browser 2>/dev/null || true)"; do
  if [ -n "$c" ] && [ -x "$c" ]; then CHROME="$c"; break; fi
done
[ -n "$CHROME" ] || { echo "ERROR: no Chrome/Chromium found for --print-to-pdf" >&2; exit 1; }

# 3. Render markdown -> styled HTML -> PDF.
TMP_HTML="$(mktemp -t handoff-XXXXXX).html"
trap 'rm -f "$TMP_HTML"' EXIT
node "$SKILL_DIR/render.js" "$IN" "$TMP_HTML"

"$CHROME" --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$OUT" "file://$TMP_HTML" 2>/dev/null

echo "Generated: $OUT"
