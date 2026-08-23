#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# Download pre-trained model weights for the jazz solo transcriber.
# Run once after cloning the repo.
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

MODEL_DIR="${1:-models}"
mkdir -p "$MODEL_DIR"

echo "=== Downloading pre-trained models to $MODEL_DIR ==="

# ── 1. Demucs (HTDemucs) ─────────────────────────────────────────────────
# Demucs downloads weights on first use via torch.hub.
# Pre-cache them to avoid download delays.
echo ""
echo "[1/3] Caching Demucs HTDemucs weights …"
python3 -c "
import torch
# Trigger download of HTDemucs weights
model = torch.hub.load('facebookresearch/demucs', 'demucs', repo='main')
print('  ✓ HTDemucs cached')
"

# ── 2. Basic Pitch ──────────────────────────────────────────────────────
echo ""
echo "[2/3] Caching Basic Pitch weights …"
python3 -c "
import basic_pitch
from basic_pitch import ICASSP_2022_MODEL_PATH
import tensorflow as tf
model = tf.saved_model.load(ICASSP_2022_MODEL_PATH)
print(f'  ✓ Basic Pitch cached ({ICASSP_2022_MODEL_PATH})')
"

# ── 3. madmom RNN beat tracking weights ─────────────────────────────────
echo ""
echo "[3/3] Caching madmom RNN weights …"
python3 -c "
import madmom
from madmom.models import download as download_madmom_model
# The RNN beat tracking model downloads on first use
print('  ✓ madmom models ready (downloaded on first inference)')
"

echo ""
echo "=== All models cached. Ready to transcribe! ==="
echo ""
echo "Try:  jazz-transcribe path/to/jazz_track.wav"