# Project state

## Completed

Added `python -m jazz_solo.lead_sheet` as a separate, experimental reading-copy exporter. It converts MIDI seconds using an explicit BPM and beat origin, resolves simultaneous detections by velocity, clips overlaps, writes visible rests and 4/4 measures, and leaves source MIDI unchanged. Two 20-second Sonny Stitt recording previews were processed locally into provisional MusicXML and PDFs; audio and output files are ignored and not shared in Git.

## Current behavior and decisions

The source recording is mixed and Demucs `other` is not an isolated saxophone. This exporter is an engraving heuristic, not a validated transcription model: louder accompaniment can win, and onset grouping can discard notes. 4/4, pulse, tempo, downbeat and 16th-grid choices must be checked; chord symbols and sax transposition are not inferred. The default transcription pipeline remains unchanged, including its pre-existing MusicXML timing issue. The exporter deliberately requires explicit tempo rather than implying automatic beat tracking is reliable.

## Tests

`python -m pytest tests/test_lead_sheet.py tests/test_pipeline.py -q` passed locally: 36 tests, with four dependency deprecation warnings. Source recordings and the Omnibook reference were inspected locally; no reference score or audio is committed.

## Next actions and blockers

Evaluate actual solo sections against a time-aligned, authorized note-level reference. Determine saxophone part and chord changes and validate tempo, downbeats, pitch and rhythm by ear. Improve sax isolation and melody tracking before claiming accuracy. Integrate the explicit tempo/beat map into the main pipeline after validating it. Existing unrelated uncommitted working-tree changes predate this work and are not included in the branch commit.
