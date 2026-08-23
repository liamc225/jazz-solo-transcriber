#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# Fine-tune Basic Pitch (or MT3) on Weimar Jazz Database data.
#
# Prerequisites:
#   1. Run scripts/download_models.sh  (once)
#   2. Run scripts/preprocess_weimar.sh (to create NPZ dataset)
#   3. This runs on a **GPU instance** — Lambda Labs / Modal / local
#
# Usage:
#   ./scripts/train.sh [dataset_path] [output_dir]
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

DATASET="${1:-weimar_processed/weimar.npz}"
OUTPUT_DIR="${2:-training_output}"
EPOCHS="${3:-50}"

echo "=== Jazz Solo Transcriber — Fine-Tuning ==="
echo "  Dataset:  $DATASET"
echo "  Output:   $OUTPUT_DIR"
echo "  Epochs:   $EPOCHS"
echo ""

cd "$(dirname "$0")/.."

# ── Check for GPU ───────────────────────────────────────────────────────
if python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null | grep -q True; then
    echo "✓ GPU detected"
else
    echo "⚠️  No GPU detected — training will be slow!"
    echo "   Consider using Lambda Labs or Modal."
fi

echo ""
echo "Starting fine-tuning …"

python3 -m jazz_solo.training.trainer \
    --dataset "$DATASET" \
    --output-dir "$OUTPUT_DIR" \
    --epochs "$EPOCHS"

echo ""
echo "=== Training complete! ==="
echo "Check $OUTPUT_DIR for model checkpoints and metrics."