"""Create an *unverified* monophonic reading copy from a detected MIDI.

This is an engraving aid, not saxophone source separation: selecting the
loudest simultaneous detection can discard the melody or retain accompaniment.
Tempo and beat origin must be checked against the recording.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import music21

from jazz_solo.utils.midi import load_midi


def build_lead_sheet(notes, tempo: float, beat_origin: float = 0.0,
                     title: str = "Unverified transcription"):
    """Convert seconds to beats and create one provisional 16th-note voice.

    beat_origin identifies a quarter-note pulse, not necessarily a downbeat.
    Simultaneous candidates are resolved by velocity; overlaps are clipped.
    The source MIDI is left untouched and remains the authoritative detection.
    """
    if not math.isfinite(tempo) or tempo <= 0 or not math.isfinite(beat_origin):
        raise ValueError("Tempo must be positive and beat origin must be finite")
    seconds_per_beat = 60.0 / tempo
    # Extend the pulse backwards to include the start of the recording.
    origin = beat_origin - math.ceil(beat_origin / seconds_per_beat) * seconds_per_beat
    candidates = {}
    for start, end, pitch, velocity in notes:
        if end <= start or start < 0:
            continue
        start_tick = max(0, round((start - origin) / seconds_per_beat * 4))
        end_tick = max(start_tick + 1, round((end - origin) / seconds_per_beat * 4))
        candidate = (velocity, end_tick, pitch)
        if start_tick not in candidates or candidate > candidates[start_tick]:
            candidates[start_tick] = candidate

    ticks = sorted(candidates)
    part = music21.stream.Part()
    part.insert(0, music21.meter.TimeSignature('4/4'))
    part.insert(0, music21.tempo.MetronomeMark(number=tempo))
    part.insert(0, music21.clef.TrebleClef())
    for index, start_tick in enumerate(ticks):
        velocity, end_tick, pitch = candidates[start_tick]
        if index + 1 < len(ticks):
            end_tick = min(end_tick, ticks[index + 1])
        note = music21.note.Note(int(pitch), quarterLength=(end_tick - start_tick) / 4)
        note.volume.velocity = int(max(0, min(127, velocity)))
        part.insert(start_tick / 4, note)
    score = music21.stream.Score()
    score.metadata = music21.metadata.Metadata(title=title)
    part.makeRests(fillGaps=True, inPlace=True)
    score.insert(0, part.makeMeasures().makeTies())
    return score


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('midi', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--tempo', required=True, type=float)
    parser.add_argument('--beat-origin', type=float, default=0.0)
    parser.add_argument('--title', default='Unverified transcription')
    args = parser.parse_args()
    score = build_lead_sheet(load_midi(args.midi), args.tempo, args.beat_origin, args.title)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    score.write('musicxml', fp=str(args.output))


if __name__ == '__main__':
    main()
