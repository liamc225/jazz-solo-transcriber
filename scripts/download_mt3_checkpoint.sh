#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# Download MT3 checkpoint for fine-tuning.
#
# MT3 is Google's Transformer-based music transcription model.
# The pre-trained checkpoint is hosted on Hugging Face or GCS.
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

MODEL_DIR="${1:-models/mt3}"
mkdir -p "$MODEL_DIR"

echo "=== Downloading MT3 checkpoint ==="
echo "  Target: $MODEL_DIR"
echo ""

# Pre-trained MT3 checkpoint URL (from magenta/mt3)
# Options:
#   - mt3_small (fastest, recommended for fine-tuning)
#   - mt3_base  (better quality, needs more GPU memory)

CHECKPOINT_URL="https://storage.googleapis.com/magentadata/models/mt3/checkpoints/mt3_small.zip"

echo "Downloading from $CHECKPOINT_URL …"
curl -L "$CHECKPOINT_URL" -o /tmp/mt3_checkpoint.zip
unzip -qo /tmp/mt3_checkpoint.zip -d "$MODEL_DIR"
rm /tmp/mt3_checkpoint.zip

echo ""
echo "✓ MT3 checkpoint → $MODEL_DIR"
ls -lh "$MODEL_DIR"/

echo ""
echo "To use MT3: set --model mt3 in transcribe command"
echo "To fine-tune: run ./scripts/train.sh with --model mt3"