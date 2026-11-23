"""Create an *unverified* monophonic reading copy from a detected MIDI.

This is an engraving aid, not saxophone source separation: selecting the
loudest simultaneous detection can discard the melody or retain accompaniment.
Tempo and beat origin must be checked against the recording.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import music21

from jazz_solo.utils.midi import load_midi


def build_lead_sheet(notes, tempo: float, beat_origin: float = 0.0,
                     title: str = "Unverified transcription",
                     downbeat_origin: float | None = None, subdivisions: int = 4,
                     key_signature: str | None = None, chords=None,
                     pitch_range: tuple[int, int] | None = None):
    """Convert seconds to beats and create one provisional monophonic voice.

    beat_origin identifies a quarter-note pulse, not necessarily a downbeat.
    Simultaneous candidates are resolved by velocity; overlaps are clipped.
    The source MIDI is left untouched and remains the authoritative detection.
    """
    if not math.isfinite(tempo) or tempo <= 0 or not math.isfinite(beat_origin):
        raise ValueError("Tempo must be positive and beat origin must be finite")
    if subdivisions not in (4, 8):
        raise ValueError("subdivisions must be 4 or 8")
    if pitch_range is not None and not (0 <= pitch_range[0] <= pitch_range[1] <= 127):
        raise ValueError("Pitch range must be ascending MIDI values from 0 to 127")
    seconds_per_beat = 60.0 / tempo
    # Extend the pulse backwards to include the start of the recording.
    if downbeat_origin is not None:
        if not math.isfinite(downbeat_origin):
            raise ValueError("Downbeat origin must be finite")
        bar_duration = 4 * seconds_per_beat
        origin = downbeat_origin - math.ceil(downbeat_origin / bar_duration) * bar_duration
    else:
        origin = beat_origin - math.ceil(beat_origin / seconds_per_beat) * seconds_per_beat
    candidates = {}
    for start, end, pitch, velocity in notes:
        if end <= start or start < 0:
            continue
        if pitch_range is not None and not (pitch_range[0] <= pitch <= pitch_range[1]):
            continue
        start_tick = max(0, round((start - origin) / seconds_per_beat * subdivisions))
        end_tick = max(start_tick + 1, round((end - origin) / seconds_per_beat * subdivisions))
        candidate = (velocity, end_tick, pitch)
        if start_tick not in candidates or candidate > candidates[start_tick]:
            candidates[start_tick] = candidate

    ticks = sorted(candidates)
    part = music21.stream.Part()
    part.insert(0, music21.meter.TimeSignature('4/4'))
    part.insert(0, music21.tempo.MetronomeMark(number=tempo))
    part.insert(0, music21.clef.TrebleClef())
    if key_signature:
        part.insert(0, music21.key.Key(key_signature))
    # Chords are supplied by the caller, never inferred from the recording.
    # A later change wins when two annotations snap to the same beat.
    harmony_by_beat = {}
    for time, figure in sorted(chords or [], key=lambda item: item[0]):
        if not math.isfinite(time):
            raise ValueError("Chord times must be finite")
        offset = max(0, round((time - origin) / seconds_per_beat))
        harmony_by_beat[offset] = re.sub(r"^([A-G])b", r"\1-", figure)
    for offset, figure in harmony_by_beat.items():
        chord = (music21.harmony.NoChord() if figure == "N.C." else
                 music21.harmony.ChordSymbol(figure))
        part.insert(offset, chord)
    for index, start_tick in enumerate(ticks):
        velocity, end_tick, pitch = candidates[start_tick]
        if index + 1 < len(ticks):
            end_tick = min(end_tick, ticks[index + 1])
        note = music21.note.Note(int(pitch), quarterLength=(end_tick - start_tick) / subdivisions)
        note.volume.velocity = int(max(0, min(127, velocity)))
        part.insert(start_tick / subdivisions, note)
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
    parser.add_argument('--downbeat-origin', type=float, default=None,
                        help='time in seconds of a verified 4/4 downbeat')
    parser.add_argument('--subdivisions', type=int, choices=(4, 8), default=4,
                        help='ticks per beat (4=sixteenths, 8=thirty-seconds)')
    parser.add_argument('--key', default=None, help='concert key, e.g. B- or F')
    parser.add_argument('--chords-json', type=Path, help='JSON list of {time, symbol} in clip seconds')
    parser.add_argument('--pitch-range', type=int, nargs=2, metavar=('LOW', 'HIGH'),
                        help='optional inclusive concert MIDI pitch range')
    args = parser.parse_args()
    chords = None
    if args.chords_json:
        chords = [(float(c['time']), c['symbol']) for c in json.loads(args.chords_json.read_text())]
    score = build_lead_sheet(load_midi(args.midi), args.tempo, args.beat_origin,
                             args.title, args.downbeat_origin, args.subdivisions,
                             args.key, chords, args.pitch_range)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    score.write('musicxml', fp=str(args.output))


if __name__ == '__main__':
    main()
