#!/usr/bin/env python3
"""Example: transcribe a jazz solo from a full recording.

Usage:
    python examples/transcribe_example.py path/to/jazz_track.wav [options]

Or after installing:
    jazz-transcribe path/to/jazz_track.wav
"""

import sys
from pathlib import Path

# Add project to path so we can run this as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jazz_solo.config import PipelineConfig, SeparatorConfig, TranscriberConfig, QuantizerConfig
from jazz_solo.pipeline.orchestrator import JazzSoloPipeline


def main():
    # Default: use a sample file or accept CLI arg
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_path = sys.argv[1]

    # ── Configure for optimal jazz transcription ─────────────────────
    config = PipelineConfig(
        separator=SeparatorConfig(
            model="htdemucs",       # Best quality separation
            shifts=3,               # Good balance of quality/speed
            stem="other",           # 'other' catches sax/trumpet/piano solos
            device="cpu",
        ),
        transcriber=TranscriberConfig(
            model="basic-pitch",    # Fast, good for monophonic solos
            onset_threshold=0.5,    # Moderate — adjust up to reduce false positives
            frame_threshold=0.3,
            minimum_note_length=0.058,  # ≈ 32nd note at 120 BPM
        ),
        quantizer=QuantizerConfig(
            grid_resolution="16th",
            swing_ratio=0.0,        # Auto-detect from the track
            min_bpm=40,
            max_bpm=400,
        ),
        verbose=True,
    )

    pipeline = JazzSoloPipeline(config)

    print(f"🎷 Transcribing: {input_path}")
    print()

    notes = pipeline.transcribe(input_path)

    if notes:
        output_dir = Path(input_path).stem + "_transcription"
        print()
        print(f"✅ Done — {len(notes)} notes transcribed")
        print(f"📁 Output: {output_dir}/")
        print(f"   ├── 01_raw_transcription.mid")
        print(f"   ├── 02_quantized_transcription.mid")
        print(f"   └── 03_transcription.musicxml")
    else:
        print("⚠️  No notes detected. Try adjusting thresholds:")
        print("   --onset-threshold 0.4 --frame-threshold 0.2")


if __name__ == "__main__":
    main()