# Exploratory Sonny Stitt benchmark

Three 20-second excerpts from recordings streamed from [Stitt's Bits](https://sonnystitt.bandcamp.com/album/stitts-bits-the-bebop-recordings-1949-1952) were compared with the [Weimar Jazz Database](https://jazzomat.hfm-weimar.de/dbformat/dboverview.html), using manually annotated solo notes. Cite the database as: Pfleiderer, Frieler, Abeßer, Zaddach and Burkhart (eds.), *Inside the Jazzomat*, Schott Campus, 2017.

The matching takes were identified by comparing note-pitch energy around annotated onsets against the available takes. The alignment was chosen on material overlapping the evaluation excerpts, so these are exploratory results, not an independent held-out evaluation. Approximate track-relative time of Weimar onset zero and crop start:

| Excerpt | WJazzD melid | Reference zero (s) | Crop start (s) |
| --- | ---: | ---: | ---: |
| Elora, take 2 | 394 | 42.747 | 50 |
| Teapot, take 2 | 396 | 48.714 | 56 |
| Blue Mode, take 1 | 391 | 121.953 | 129 |

Audio is not committed. The local run used the pre-existing uncommitted working-tree pipeline fixes (including the Demucs segment fix) and Core ML inference. With 0.25 seconds excluded at each edge and a 50 ms onset tolerance, note F1 counts one-to-one onset-and-pitch matches, using 50 cents pitch tolerance and ignoring offsets:

| Recording | Reference notes | Raw note F1 | Original swing-quantized F1 | Straight-quantized F1 |
| --- | ---: | ---: | ---: | ---: |
| Elora | 105 | 0.694 | 0.421 | 0.583 |
| Teapot | 130 | 0.705 | 0.330 | 0.528 |
| Blue Mode | 75 | 0.807 | 0.453 | 0.690 |

The straight-grid measurements used the existing raw MIDI and the revised quantizer, not a second separation/model run. Beat tracking and Demucs can vary; use the saved MIDI for exact replication. These values do not measure note duration, score readability, or correctness of harmony. The quantizer remains less accurate than raw timing.

Reading-copy output uses annotation-derived average tempo and downbeat. After fixing evaluation to merge tied notes before counting them, the unfiltered reading-copy note F1 is 0.676/0.605/0.356 on a 16th grid and 0.734/0.719/0.735 on a 32nd grid (Elora/Teapot/Blue Mode). Earlier versions of this report counted tied note segments as separate attacks; those reading-copy figures have been replaced. These scores are not comparable to fully automatic inference: they use reference-derived tempo/downbeats and a constant-tempo approximation.

The newer reading copies additionally use the Weimar key signatures and chord annotations, and an explicitly selected concert MIDI range of 48–84. Their tie-merged onset-and-pitch F1 values are 0.740, 0.736 and 0.735. The range was chosen after inspecting these same examples, so these are exploratory and cannot establish generalization. Key and harmony were supplied by the database, not inferred by the audio model. Chord changes are mapped to the nearest beat of a constant-tempo approximation and need review; the estimated melody, rhythm, articulation and accidental spelling also need review. These changes do not alter or retrain the detector.

To evaluate MusicXML instead of MIDI, add `--score-tempo BPM --score-origin SECONDS` to the benchmark command. The origin is the audio time corresponding to notated score time zero. This evaluates straight playback of the notation and merges ties; it does not evaluate swing playback or note offsets. `python -m jazz_solo.training.weimar_harmony DATABASE OUTPUT --melid ID --reference-zero SECONDS --crop-start SECONDS --score-start SECONDS --duration 20` produces a chord JSON file; `python -m jazz_solo.lead_sheet MIDI OUTPUT --tempo BPM --downbeat-origin SECONDS --key B- --chords-json FILE --pitch-range 48 84 --subdivisions 8` uses explicit harmony and pitch constraints. Adapt key, range, timing and resolution to the piece. Never assume the filtered range applies to every saxophone recording.

`python -m jazz_solo.training.benchmark_weimar DATABASE MIDI --melid ID --reference-zero SECONDS --crop-start SECONDS --duration 20` reproduces the note comparison after the alignment and files are supplied. The caller must verify the correct take and alignment. Avoid evaluating a different master, performance, or take as if synchronized.

## Remaining work

Use independent calibration and held-out evaluation; increase the number and diversity of solos; test note offsets and transcription duration; validate notated rhythm and downbeats by ear; handle changing tempo; isolate the saxophone better; support chord changes and spelling rather than claiming a finished Omnibook-style score. Fix the main MusicXML export's seconds-to-beats conversion and propagate the detected beat map. The pipeline now emits an additional tempo-aware 04 reading copy using the estimated beat map; the legacy 03 MusicXML output still needs its seconds-to-beats conversion fixed. Automatic key and harmony recognition remain unsupported.

## Swing-style notation experiment

The optional `--rhythm jazz --swing-ratio 0.6` reading mode maps a performed long-short pair onto written even eighths, favors the eighth grid, and uses sixteenths for some faster attacks. It can merge or omit simultaneous candidates, rounds note lengths, and can close short gaps. It does not alter raw MIDI. `05_swing_reading.musicxml` is generated alongside the more detailed `04` copy by the pipeline, using its estimated beat map and an assumed 0.6 swing ratio. Neither output is a verified transcription.

Using the same three examples, annotated key, harmony, tempo and approximate phase as above, a 48–84 pitch filter, and 0.6 swing playback, the readable swing drafts' onset-and-pitch F1 scores are 0.651, 0.506 and 0.497 for Elora, Teapot and Blue Mode. These are lower than the detailed drafts' previously reported 0.740, 0.736 and 0.735, which were evaluated with straight playback. Different playback assumptions and 50 ms tolerance limit the direct comparison, but the coarse grid also drops or merges detected notes. The user should not treat the simpler notation as an accuracy improvement. We changed Blue Mode's notated quarter pulse from 60.7 to 121.4 BPM, redistributing bar lines as a double-time reading; this is an editorial choice, not a verified change in the underlying meter. Automatic copies use the estimated pulse and do not make that choice.

The swing drafts are still exploratory: alignment was fitted on overlapping audio, the pitch range was selected after observing the same examples, durations and offset accuracy were not evaluated, and chords were supplied by Weimar rather than detected. Extend the evaluation to held-out takes and improve onset modeling before relying on these scores for study.
