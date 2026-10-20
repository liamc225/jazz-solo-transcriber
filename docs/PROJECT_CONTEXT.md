# Jazz Solo Transcriber: project context (agent handoff)

_Last updated: Oct 20, 2026. **This repository is public.**_

## What it is and who it's for
A Python pipeline that turns jazz recordings into quantized MIDI and MusicXML transcriptions of the solo. It's for jazz musicians and students who transcribe solos, and for anyone experimenting with music-transcription models.

## Stack
Python 3.10+, installed as the `jazz-transcribe` CLI (Click). The pipeline has three stages:
- Stage A, source separation: Demucs/HTDemucs.
- Stage B, pitch and onset detection: Basic Pitch, or MT3 with a checkpoint.
- Stage C, metrical alignment and quantization: madmom/librosa, with swing detection.

Output is MIDI plus MusicXML (music21). There's also a fine-tuning and eval harness for the Weimar Jazz Database (`jazz_solo/training/`, mir_eval).

## Deploy
None. It's a local CLI and library. Model weights come from `scripts/download_models.sh` and `scripts/download_mt3_checkpoint.sh`. Training needs a GPU (`scripts/train.sh`). There are no CI workflows.

## Live URLs
This public GitHub repository. There is no separate site.

## Status
There's a single initial commit (Aug 23, 2026). There are no open PRs or issues and no recorded benchmark results.

## Open tasks and next steps
1. Run `tests/` and an end-to-end transcription of a sample track, and record actual quality metrics (onset/note F1).
2. Add CI (pytest) and pin working dependency versions (madmom and torch compatibility).
3. Try Weimar fine-tuning on a cloud GPU and compare it against stock Basic Pitch.

## Standing rules
- No personal name or face on anything public. This repo is public, so commits, docs, and package metadata should use the project brand, Jazz Solo Transcriber.
- Don't commit model weights, datasets, or copyrighted audio.

## Where secrets live
None needed. Never commit tokens (for example, a Hugging Face token) if one is added later.
