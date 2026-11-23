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
                     pitch_range: tuple[int, int] | None = None,
                     rhythm: str = "precise", swing_ratio: float = 0.6):
    """Convert seconds to beats and create one provisional monophonic voice.

    beat_origin identifies a quarter-note pulse, not necessarily a downbeat.
    Simultaneous candidates are resolved by velocity; overlaps are clipped.
    The source MIDI is left untouched and remains the authoritative detection.
    """
    if not math.isfinite(tempo) or tempo <= 0 or not math.isfinite(beat_origin):
        raise ValueError("Tempo must be positive and beat origin must be finite")
    if rhythm not in ("precise", "jazz"):
        raise ValueError("rhythm must be precise or jazz")
    if not 0.5 <= swing_ratio <= 0.75:
        raise ValueError("swing ratio must be between 0.5 and 0.75")
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
    # Jazz charts conventionally notate swung eighths evenly and leave the
    # long-short feel to performance. The source MIDI remains unchanged.
    if rhythm == "jazz":
        subdivisions = 4  # sixteenths are available for genuinely faster figures

    def notation_beat(time):
        beat = (time - origin) / seconds_per_beat
        if rhythm != "jazz":
            return beat
        whole = math.floor(beat)
        phase = beat - whole
        if phase <= swing_ratio:
            return whole + .5 * phase / swing_ratio
        return whole + .5 + .5 * (phase - swing_ratio) / (1 - swing_ratio)

    candidates = {}
    for start, end, pitch, velocity in sorted(notes, key=lambda n: n[0]):
        if end <= start or start < 0:
            continue
        if pitch_range is not None and not (pitch_range[0] <= pitch <= pitch_range[1]):
            continue
        beat = max(0.0, notation_beat(start))
        if rhythm == "jazz":
            # Prefer the eighth-note pulse when reasonably close; use a
            # sixteenth for a faster attack or an occupied eighth slot.
            eighth_tick = max(0, round(beat * 2) * 2)
            start_tick = eighth_tick if abs(beat - eighth_tick / 4) <= .20 else round(beat * 4)
            if start_tick in candidates:
                alternatives = [t for t in (start_tick - 1, start_tick + 1)
                                if t >= 0 and t not in candidates and abs(beat - t / 4) <= .06]
                if alternatives:
                    start_tick = min(alternatives, key=lambda t: abs(beat - t / 4))
            end_tick = max(start_tick + 2, round(notation_beat(end) * 2) * 2)
        else:
            start_tick = max(0, round(beat * subdivisions))
            end_tick = max(start_tick + 1, round(notation_beat(end) * subdivisions))
        candidate = (velocity, end_tick, pitch)
        if start_tick not in candidates or candidate > candidates[start_tick]:
            candidates[start_tick] = candidate

    ticks = sorted(candidates)
    part = music21.stream.Part()
    part.insert(0, music21.meter.TimeSignature('4/4'))
    part.insert(0, music21.tempo.MetronomeMark(
        text="Swing" if rhythm == "jazz" else None, number=tempo))
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
            next_tick = ticks[index + 1]
            if rhythm == "jazz" and 0 < next_tick - end_tick <= 1:
                end_tick = next_tick
            end_tick = min(end_tick, next_tick)
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
    parser.add_argument('--rhythm', choices=('precise', 'jazz'), default='precise')
    parser.add_argument('--swing-ratio', type=float, default=.6,
                        help='performed offbeat fraction for jazz notation')
    args = parser.parse_args()
    chords = None
    if args.chords_json:
        chords = [(float(c['time']), c['symbol']) for c in json.loads(args.chords_json.read_text())]
    score = build_lead_sheet(load_midi(args.midi), args.tempo, args.beat_origin,
                             args.title, args.downbeat_origin, args.subdivisions,
                             args.key, chords, args.pitch_range, args.rhythm, args.swing_ratio)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    score.write('musicxml', fp=str(args.output))


if __name__ == '__main__':
    main()
