# Project state

## Completed

Added `python -m jazz_solo.lead_sheet` as a separate, experimental reading-copy exporter. It converts MIDI seconds using an explicit BPM and beat origin, resolves simultaneous detections by velocity, clips overlaps, writes visible rests and 4/4 measures, and leaves source MIDI unchanged. Two 20-second Sonny Stitt recording previews were processed locally into provisional MusicXML and PDFs; audio and output files are ignored and not shared in Git.

## Current behavior and decisions

The source recording is mixed and Demucs `other` is not an isolated saxophone. This exporter is an engraving heuristic, not a validated transcription model: louder accompaniment can win, and onset grouping can discard notes. 4/4, pulse, tempo, downbeat and 16th-grid choices must be checked; chord symbols and sax transposition are not inferred. The main pipeline now also emits a separate tempo-aware reading copy using its estimated beat map; the legacy 03 MusicXML output still has a seconds-to-beats timing issue. The standalone exporter accepts explicit tempo and optional reference harmony.

## Tests

`python -m pytest tests/test_lead_sheet.py tests/test_pipeline.py -q` passed locally: 36 tests, with four dependency deprecation warnings. Source recordings and the Omnibook reference were inspected locally; no reference score or audio is committed.

## Next actions and blockers

Evaluate actual solo sections against a time-aligned, authorized note-level reference. Determine saxophone part and chord changes and validate tempo, downbeats, pitch and rhythm by ear. Improve sax isolation and melody tracking before claiming accuracy. Integrate the explicit tempo/beat map into the main pipeline after validating it. Existing unrelated uncommitted working-tree changes predate this work and are not included in the branch commit.

## Sonny Stitt benchmark update

Matched WJazzD solos to Elora take 2, Teapot take 2 and Blue Mode take 1 using note-pitch energy and approximate alignment; cut 20-second local excerpts. Raw note F1 at 50 ms is 0.694/0.705/0.807, versus 0.421/0.330/0.453 under the old swing quantizer. The revised default straight grid yields 0.583/0.528/0.690 on saved raw MIDI. Alignment was fitted on overlapping material, so results are exploratory, not held out. `docs/stitt-benchmark.md` records offsets, methodology, limitations, and sources. Recordings and scores remain local and ignored.

Fixed the evaluator's MIDI-to-Hz conversion, pitch-accuracy calculation and swapped onset metrics; added a WJazzD benchmark CLI. Default quantization no longer automatically applies an unreliable swing estimate; explicitly requested swing now warps sixteenth positions correctly. The reading-copy exporter accepts an explicit downbeat and a 32nd-note grid; generated three provisional PDF/MusicXML scores locally using annotation-derived tempo and downbeat. These scores still have false positives, approximated rhythms, and no chords. The main pipeline MusicXML timing bug remains unresolved. The pre-existing uncommitted project work is not included in these commits and was used for local inference; test a clean checkout separately.

Verification for this update: the complete local working-tree suite passed 44 tests (four dependency deprecation warnings). The staged clean checkout passed 35 tests, including all 11 new/updated benchmark, scoring, quantization and reading-copy tests. Full audio inference was performed with the pre-existing local fixes, not a clean checkout.

## Reference-style reading copies

Added opt-in concert key, explicitly supplied timed chord symbols, and optional concert MIDI pitch-range filtering to the reading-copy exporter. Added a Weimar harmony extraction utility that validates and converts common chord spellings; the recording take and alignment remain the caller's responsibility. Regenerated the three local Stitt PDF/MusicXML drafts with annotation-derived key/chords and an explicitly chosen 48–84 pitch range. The harmony is reference-assisted, not detected by the audio model, and chord placement uses approximate constant-tempo beat mapping. The chosen range was evaluated on the same three excerpts and is not a validated universal saxophone range.

Fixed the reading-copy benchmark to merge tied notes and exclude chord symbols. Corrected the earlier reading-copy F1 figures in `docs/stitt-benchmark.md`; newer drafts score 0.740/0.736/0.735 for Elora/Teapot/Blue Mode at 50 ms onset tolerance, using reference tempo/downbeat and same-data alignment. They are preliminary and do not assess note offsets, swing playback, phrasing or chord accuracy. Main pipeline MusicXML timing remains unresolved; these are reading-copy outputs, not polished scores or a retrained model.


## Automatic reading-copy output

The full pipeline now emits `04_reading_copy.musicxml` from raw note detections and its estimated beat map. This is a provisional one-voice reading copy: detected tempo/beat origin may be wrong, its downbeats are not verified, and it includes no inferred key or chords. The existing raw MIDI, quantized MIDI and legacy 03 MusicXML remain available. A full pipeline run on the local Elora excerpt successfully generated the new output. Full local suite: 54 passed (four dependency deprecation warnings); full inference still uses the pre-existing uncommitted local dependency and Demucs fixes.

The staged clean checkout for the reference-style and pipeline integration update passed all 45 tests. The local working tree passed 54 tests with four dependency warnings.

## Swing-notation revision

Added optional `rhythm='jazz'` / `--rhythm jazz`, which treats a configurable long-short performed pair (default 0.6 offbeat) as written even eighths, prefers eighth-note positions, uses some sixteenths for faster events, and simplifies short articulation gaps. The main pipeline now writes `05_swing_reading.musicxml` in addition to the more detailed `04` copy; neither has inferred harmony and both remain unverified. The raw notes are unchanged. Verified the full local Elora run created 05; this run still depends on pre-existing uncommitted local fixes.

Regenerated three local PDF drafts with reference-supplied key/chords, 48–84 pitch filter, and swing notation. Elora has 71 eighths and 23 sixteenths; Teapot has 51 eighths and 52 sixteenths; the Blue Mode draft uses a 121.4 BPM double-time notation and has 42 eighths and 27 sixteenths. The Blue Mode bar lines were redistributed as an editorial choice rather than verified original meter. When evaluated with 0.6 swing playback, note F1 is 0.651/0.506/0.497; the simpler output loses or merges notes and is not more accurate. The detailed 04 and raw MIDI remain the safer basis for correction. Benchmark evaluator now supports swing playback and merges ties. See `docs/stitt-benchmark.md` for comparison limits and further work.

Verification for swing revision: local full suite passed 58 tests (four dependency warnings); staged clean checkout passed 49 tests. The swing draft PDFs were rendered and visually inspected locally.

## Guitar trials

Processed twelve 20-second excerpts across Wes Montgomery, Grant Green and Joe Pass recordings (four per artist); all twelve local pipeline runs completed, and their guitar-clef PDF, MusicXML and raw MIDI drafts are packaged under ignored `outputs/guitar_trials/`. Details, source album links and excerpt times are in `docs/guitar-trials.md`. The passages on Wes/Grant recordings have not been confirmed as guitar solos by ear, and there is no matched human reference or accuracy score. Joe's unaccompanied guitar is polyphonic; the one-line drafts lose accompaniment and chords, while separated Wes/Grant stems may contain other instruments. No audio or score artifacts were committed.

Added optional time-signature support and an octave-lower guitar clef in `lead_sheet`, retaining sounding MIDI pitches in MusicXML. Drafts use an explicit 40–88 guitar range; West Coast Blues uses 6/4 from an external abridged annotation, but downbeat alignment remains unverified. How Insensitive is rendered straight. Basic note and rendering tests passed locally; exact results and remaining limitations are recorded in `docs/guitar-trials.md`.

Verification for guitar update: 61 tests passed in the local working tree (four dependency warnings); 52 tests passed in a staged clean checkout. All twelve final PDFs were rendered and visually inspected; they remain unverified musical drafts.

## Guitar transcription research and validation

Researched and visually inspected guitar transcription PDFs; source links and layout observations are in `docs/guitar-transcription-research.md`. The same-album 1960 Four on Six score marks roughly 200 BPM and two flats; the earlier 103 BPM estimate was likely half-time. Added optional explicit system breaks and velocity cutoff to the reading-copy exporter. The local revised Four on Six 20-second PDF/MusicXML uses a doubled estimated 207 BPM, G-minor key signature, guitar octave clef, four-bar systems, swing, and a 50–84 pitch range with velocity cutoff 40. These are excerpt-specific assumptions, not verified automatic inference; chords are intentionally omitted pending alignment. A six-note pitch phrase from the source PDF matches the revised output around clip seconds 0.94–1.69, but the remainder, rhythm and exact downbeat remain unverified. Original MIDI and earlier draft are preserved under ignored outputs.

Added `benchmark_guitarset` for local GuitarSet JAMS/MIDI onset-and-pitch scoring. Evaluated four exploratory jazz guitar excerpts at several cutoffs, fixed the cutoff at velocity 60, and then evaluated two additional previously unseen players: F1 0.730→0.821 and 0.895→0.921 with a 40–88 pitch filter in both comparisons. Dataset is isolated acoustic guitar, not historical mixed recordings; only two held-out excerpts were checked and offsets are not scored. The historical spot check contains a true note at velocity 53, so do not apply cutoff 60 by default. Full details, dataset citation, methods and limitations are in `docs/guitarset-evaluation.md`; no source audio, score, annotation, or generated PDF is committed.

Verification for research update: 66 tests passed in the local working tree (four dependency warnings), and 57 passed in a staged clean checkout. The revised Four on Six PDF was rendered and visually inspected. The only matched reference phrase comprises six notes; no claim is made about the accuracy of the remaining score.
