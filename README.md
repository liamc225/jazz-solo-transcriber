# 🎷 Jazz Solo Transcriber

> **Agents / new contributors:** start with [docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md).

**AI-powered jazz solo transcription pipeline.**  
Transform raw jazz recordings into quantized MIDI and MusicXML scores.

## Architecture

```
┌─────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│  Stage A            │    │  Stage B              │    │  Stage C             │
│  Source Separation  │───▶│  Pitch & Onset Detect │───▶│  Metrical Alignment  │
│  (Demucs/HTDemucs)  │    │  (Basic Pitch / MT3)  │    │  (madmom / librosa)  │
│  Isolate the soloist│    │  Audio → MIDI notes   │    │  Quantize to grid    │
└─────────────────────┘    └──────────────────────┘    └──────────────────────┘
```

## Quick Start

```bash
# 1. Install
git clone <repo>
cd jazz-solo-transcriber
pip install -e .

# 2. Download model weights
./scripts/download_models.sh

# 3. Transcribe!
jazz-transcribe path/to/jazz_track.wav
```

## CLI Usage

```bash
# Basic transcription
jazz-transcribe my_jazz_track.wav

# Skip source separation (input is already a solo track)
jazz-transcribe solo_track.wav --skip-separation

# Adjust detection thresholds for dense bebop
jazz-transcribe bird_solo.wav --onset-threshold 0.4 --frame-threshold 0.2

# Use MT3 backend (requires MT3 checkpoint)
jazz-transcribe track.wav --transcriber mt3

# Info about a transcribed MIDI file
jazz-transcribe info transcription.mid
```

## Output

```
my_jazz_track_transcription/
├── other.wav                    # Isolated solo stem (Stage A)
├── 01_raw_transcription.mid     # Direct from transcriber (Stage B)
├── 02_quantized_transcription.mid  # Rhythmically quantized (Stage C)
└── 03_transcription.musicxml    # Import into any score editor
```

## Fine-Tuning (GPU Required)

For training your own models on the [Weimar Jazz Database](https://jazzomat.hfm-weimar.de/dbformat/dbformat.html):

```bash
# 1. Download the Weimar Jazz Database
#    (available at https://jazzomat.hfm-weimar.de)

# 2. Preprocess into spectrogram/MIDI pairs
./scripts/preprocess_weimar.sh /path/to/weimar_jazz_db

# 3. Train on GPU
./scripts/train.sh weimar_processed/weimar.npz training_output 50
```

## Evaluation

```python
from jazz_solo.training.evaluate import TranscriptionEvaluator

ev = TranscriptionEvaluator(onset_tolerance=0.05)
metrics = ev.evaluate_file("my_transcription.mid", "ground_truth.mid")
print(metrics)
# {'onset_f1': 0.85, 'note_f1': 0.82, ...}
```

## Configuration

All pipeline parameters are configurable via `jazz_solo.config`:

| Component    | Key Parameter         | Default     | Description                             |
|-------------|-----------------------|-------------|-----------------------------------------|
| Separator   | `model`               | `htdemucs`  | Demucs model variant                    |
| Separator   | `stem`                | `other`     | Stem to extract (vocals/other/drums/... |
| Transcriber | `model`               | `basic-pitch` | Backend: basic-pitch or mt3             |
| Transcriber | `onset_threshold`     | `0.5`       | Onset sensitivity (lower = more notes)  |
| Quantizer   | `grid_resolution`     | `16th`      | Quantization grid                       |
| Quantizer   | `swing_ratio`         | `0.0`       | 0=auto, 0.33=straight, 0.67=heavy swing |

## Project Structure

```
jazz_solo/
├── config.py              # All configuration dataclasses
├── cli.py                 # Click CLI
├── pipeline/
│   ├── separator.py       # Stage A: Demucs
│   ├── transcriber.py     # Stage B: Basic Pitch / MT3
│   ├── quantizer.py       # Stage C: madmom + quantization
│   └── orchestrator.py    # Pipeline coordinator
├── training/
│   ├── dataset.py         # Weimar Dataset preprocessor
│   ├── trainer.py          # Fine-tuning harness
│   └── evaluate.py        # mir_eval evaluation
└── utils/
    ├── audio.py            # Audio I/O, spectrograms
    └── midi.py             # MIDI read/write, MusicXML export
```

## Requirements

- Python ≥ 3.10
- 4 GB+ RAM (8 GB+ recommended for Demucs)
- GPU recommended for training (CPU works for inference)

**Key dependencies:** Demucs, Basic Pitch, madmom, librosa, mir_eval, pretty_midi, music21, torch, click, numpy, scipy
