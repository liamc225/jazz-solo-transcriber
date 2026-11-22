# Project state

## Completed

Added `python -m jazz_solo.lead_sheet` as a separate, experimental reading-copy exporter. It converts MIDI seconds using an explicit BPM and beat origin, resolves simultaneous detections by velocity, clips overlaps, writes visible rests and 4/4 measures, and leaves source MIDI unchanged. Two 20-second Sonny Stitt recording previews were processed locally into provisional MusicXML and PDFs; audio and output files are ignored and not shared in Git.

## Current behavior and decisions

The source recording is mixed and Demucs `other` is not an isolated saxophone. This exporter is an engraving heuristic, not a validated transcription model: louder accompaniment can win, and onset grouping can discard notes. 4/4, pulse, tempo, downbeat and 16th-grid choices must be checked; chord symbols and sax transposition are not inferred. The default transcription pipeline remains unchanged, including its pre-existing MusicXML timing issue. The exporter deliberately requires explicit tempo rather than implying automatic beat tracking is reliable.

## Tests

`python -m pytest tests/test_lead_sheet.py tests/test_pipeline.py -q` passed locally: 36 tests, with four dependency deprecation warnings. Source recordings and the Omnibook reference were inspected locally; no reference score or audio is committed.

## Next actions and blockers

Evaluate actual solo sections against a time-aligned, authorized note-level reference. Determine saxophone part and chord changes and validate tempo, downbeats, pitch and rhythm by ear. Improve sax isolation and melody tracking before claiming accuracy. Integrate the explicit tempo/beat map into the main pipeline after validating it. Existing unrelated uncommitted working-tree changes predate this work and are not included in the branch commit.

## Sonny Stitt benchmark update

Matched WJazzD solos to Elora take 2, Teapot take 2 and Blue Mode take 1 using note-pitch energy and approximate alignment; cut 20-second local excerpts. Raw note F1 at 50 ms is 0.694/0.705/0.807, versus 0.421/0.330/0.453 under the old swing quantizer. The revised default straight grid yields 0.583/0.528/0.690 on saved raw MIDI. Alignment was fitted on overlapping material, so results are exploratory, not held out. `docs/stitt-benchmark.md` records offsets, methodology, limitations, and sources. Recordings and scores remain local and ignored.

Fixed the evaluator's MIDI-to-Hz conversion, pitch-accuracy calculation and swapped onset metrics; added a WJazzD benchmark CLI. Default quantization no longer automatically applies an unreliable swing estimate; explicitly requested swing now warps sixteenth positions correctly. The reading-copy exporter accepts an explicit downbeat and a 32nd-note grid; generated three provisional PDF/MusicXML scores locally using annotation-derived tempo and downbeat. These scores still have false positives, approximated rhythms, and no chords. The main pipeline MusicXML timing bug remains unresolved. The pre-existing uncommitted project work is not included in these commits and was used for local inference; test a clean checkout separately.

Verification for this update: the complete local working-tree suite passed 44 tests (four dependency deprecation warnings). The staged clean checkout passed 35 tests, including all 11 new/updated benchmark, scoring, quantization and reading-copy tests. Full audio inference was performed with the pre-existing local fixes, not a clean checkout.
