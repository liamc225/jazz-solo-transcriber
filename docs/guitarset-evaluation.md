# GuitarSet jazz-guitar check

Source: Xi, Bittner, Pauwels, Ye and Bello, “GuitarSet: A Dataset for Guitar Transcription,” ISMIR 2018; [GuitarSet v1.1.0](https://zenodo.org/records/3371780). GuitarSet consists of acoustic guitar recordings with per-string time-aligned annotations. It is not a recording of Wes Montgomery, Grant Green or Joe Pass. The dataset authors document some annotation errors; none of the selected IDs below are the two specifically identified as timing problems.

We extracted the matching mono-microphone WAV and per-string JAMS files for six jazz solo recordings. These are clean isolated guitar examples, unlike the mixed historical recordings. The local files and resulting MIDI are ignored and are not committed. The pre-existing local inference fixes were used; this run is not a clean-checkout end-to-end reproduction.

We ran Basic Pitch on each complete WAV with source separation skipped. GuitarSet `note_midi` events from all strings were combined and rounded to the nearest MIDI semitone. The metric is one-to-one note onset and pitch F1 with 50 ms onset tolerance and 50 cents pitch tolerance; offsets are not evaluated. Both columns apply the same 40–88 MIDI pitch range, and the second additionally removes model events with MIDI velocity below 60. Velocity is the model's scaled output amplitude, not a calibrated probability.

| Split | GuitarSet ID | F1, no cutoff | F1, cutoff 60 |
| --- | --- | ---: | ---: |
| Exploratory | 00_Jazz1-200-B_solo | 0.746 | 0.882 |
| Exploratory | 01_Jazz2-187-F#_solo | 0.739 | 0.806 |
| Exploratory | 02_Jazz3-150-C_solo | 0.882 | 0.910 |
| Exploratory | 03_Jazz2-110-Bb_solo | 0.845 | 0.934 |
| Held out after fixing cutoff | 04_Jazz1-130-D_solo | 0.730 | 0.821 |
| Held out after fixing cutoff | 05_Jazz2-110-Bb_solo | 0.895 | 0.921 |

The first four were inspected at multiple cutoffs and therefore are not held out. The cutoff of 60 was fixed before the last two players' recordings were fetched and evaluated. This is a tiny validation set with no uncertainty interval; it does not establish that the cutoff helps electric guitar in a jazz ensemble or the final printed notation. In particular, the Wes Montgomery example below contains a true detected note at velocity 53 that cutoff 60 would remove. Keep this setting opt-in and retain the raw MIDI.

Example command after obtaining a matching local WAV/JAMS pair and transcription MIDI:

```sh
python -m jazz_solo.training.benchmark_guitarset example.jams prediction.mid --pitch-range 40 88 --min-velocity 60
```

## Historical-recording spot check

[Peter Martin's score for the 1960 “Four on Six” recording](https://static1.squarespace.com/static/5cc71b1eb10f257bd04b072f/t/5dfaab36dd325c224e996f36/1576708920034/Four%2Bon%2BSix%2B-%2BWes%2BMontgomery%2B-%2BMelody%2Band%2BSolo%2B-%2BScore.pdf) names the same album, not an alternate live take. Its first page marks approximately 200 BPM and a two-flat key signature; page 5, measure 77 begins with a six-note melodic phrase. The local 2025-remaster 1:30–1:50 clip's model notes contain a matching six-note pitch sequence around 0:00.96–0:01.72. The earlier displayed line had a low accompaniment candidate replace one of these notes. A draft using a 50–84 pitch range and velocity cutoff 40 preserves the sequence, with the tempo raised from the tracker's 103 to 207 BPM as a plausible double-time interpretation. The beat/downbeat phase remains approximate; this is a spot check of six pitches, not a full alignment, rhythm/offset verification, or measured score-level improvement. The range and cutoff were selected with knowledge of that phrase and could remove correct notes elsewhere.

The revised PDF and MusicXML are local ignored files, `outputs/guitar_trials/wes_four_on_six_study_draft.*`. They use standard guitar octave clef, key signature and four-bar systems, with implied swing, but omit chord changes because the excerpt's harmonic/downbeat alignment is not independently verified. No published notes, score images, or audio are committed.
