#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# Preprocess the Weimar Jazz Database for fine-tuning.
#
# Usage:
#   ./scripts/preprocess_weimar.sh /path/to/weimar_jazz_db [output_dir]
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

WEIMAR_ROOT="${1:?Usage: $0 /path/to/weimar_jazz_db [output_dir]}"
OUTPUT_DIR="${2:-weimar_processed}"

echo "=== Preprocessing Weimar Jazz Database ==="
echo "  Source:  $WEIMAR_ROOT"
echo "  Output:  $OUTPUT_DIR"
echo ""

cd "$(dirname "$0")/.."

python3 -m jazz_solo.training.dataset "$WEIMAR_ROOT" --output-dir "$OUTPUT_DIR"

echo ""
echo "=== Done! ==="
echo "Output files:"
ls -lh "$OUTPUT_DIR"/
echo ""
echo "Next step: ./scripts/train.sh $OUTPUT_DIR"