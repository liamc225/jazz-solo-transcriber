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

Reading-copy output, with the annotation-derived average tempo and downbeat supplied as prior information, improved note F1 from 0.658 to 0.703 for Elora, 0.611 to 0.723 for Teapot, and 0.356 to 0.726 for Blue Mode when switching from a 16th to a 32nd grid. These scores are not comparable to fully automatic inference: they use reference-derived tempo/downbeats and a constant-tempo approximation, and the values include the reading-copy note selection and segmentation. They do not prove improved pitch detection.

`python -m jazz_solo.training.benchmark_weimar DATABASE MIDI --melid ID --reference-zero SECONDS --crop-start SECONDS --duration 20` reproduces the note comparison after the alignment and files are supplied. The caller must verify the correct take and alignment. Avoid evaluating a different master, performance, or take as if synchronized.

## Remaining work

Use independent calibration and held-out evaluation; increase the number and diversity of solos; test note offsets and transcription duration; validate notated rhythm and downbeats by ear; handle changing tempo; isolate the saxophone better; support chord changes and spelling rather than claiming a finished Omnibook-style score. Fix the main MusicXML export's seconds-to-beats conversion and propagate the detected beat map. The experimental reading-copy exporter is a separate path and does not fix the main pipeline's MusicXML output.
