# Guitar transcription trials

Twelve 20-second excerpts were processed from three releases. These are recording excerpts, not verified complete solos, and no note-level reference or accuracy score was available. The exact improvised-solo boundaries in Wes and Grant excerpts have not been verified by ear. Joe Pass's *Virtuoso* is solo guitar, but its simultaneous melody, bass and chord voicings cannot be preserved in a one-voice reading copy.

| Artist | Recording | Excerpt start |
| --- | --- | --- |
| Wes Montgomery | Airegin | 0:55 |
| Wes Montgomery | D-Natural Blues | 1:05 |
| Wes Montgomery | Four On Six | 1:30 |
| Wes Montgomery | West Coast Blues | 1:40 |
| Grant Green | Oleo | 0:55 |
| Grant Green | How Insensitive (Insensatez) | 1:05 |
| Grant Green | United Blues | 1:15 |
| Grant Green | Sonnymoon for Two | 1:05 |
| Joe Pass | Night And Day | 0:45 |
| Joe Pass | How High The Moon | 0:50 |
| Joe Pass | Cherokee | 0:50 |
| Joe Pass | All The Things You Are | 0:50 |

Sources: [The Incredible Jazz Guitar of Wes Montgomery](https://wesmontgomery.bandcamp.com/album/the-incredible-jazz-guitar-of-wes-montgomery-remastered-2025), [Funk in France](https://grantgreen.bandcamp.com/album/funk-in-france-from-paris-to-antibes-1969-1970), and [Virtuoso](https://joepass.bandcamp.com/album/virtuoso-remastered-2025). The Grant release includes live funk, ballad and blues material as well as bebop-related playing; it is not all bebop. The 2025 releases are remasters of earlier recordings.

The Wes and Grant clips were separated with Demucs `other` before Basic Pitch; Joe was processed without separation. Separation does not isolate guitar from piano or other instruments reliably. The local outputs include a raw MIDI, a swing-oriented reading-copy MusicXML, and a PDF for each excerpt. The reading copies are monophonic and may omit detected notes, merge attacks, or pick bass/accompaniment instead of the melody. They were rendered with the guitar octave-lower clef and an explicit sounding MIDI range 40–88; out-of-range notes were filtered, including potentially valid notes. No key signatures or chord symbols were inferred.

Tempo and beat phase were estimated and may be wrong or at half/double tempo. Meter is assumed 4/4 except West Coast Blues, which was rendered in 6/4 following the [Jazz Audio-Aligned Harmony annotation for an abridged performance](https://mtg.github.io/JAAH/data/west_coast_blues.html); the exact beat alignment between that annotation and the 2025 remaster is unverified. How Insensitive was rendered with straight rather than swing notation. No audio or generated scores are committed; the local ignored output directory holds the 12 scores, excerpts, and `jazz_guitar_draft_bundle.zip` (PDF, MusicXML and raw MIDI, with no audio).

## Next action

Find permitted, time-aligned note-level guitar references from the same recorded takes and evaluate pitches/onsets, durations and polyphony on held-out excerpts. Verify guitar solo boundaries and meter by listening. Compare separation to the original audio, add melody tracking or score-informed source separation, and support polyphonic notation or explicitly scoped single-note choruses before presenting these as reliable study scores.
