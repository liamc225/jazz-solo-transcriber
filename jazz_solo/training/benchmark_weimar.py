"""Evaluate a local MIDI against a time-aligned Weimar Jazz Database excerpt.

The database and audio must be obtained independently. No alignment or take
identification is inferred: the caller must supply the verified mapping.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from jazz_solo.training.evaluate import TranscriptionEvaluator
from jazz_solo.utils.midi import load_midi


def reference_excerpt(database: Path, melid: int, reference_zero: float,
                      crop_start: float, duration: float, margin: float = 0.25):
    """Map Weimar solo-relative notes to clip time; exclude boundary onsets.

    reference_zero is the recording time corresponding to Weimar onset zero.
    crop_start is the excerpt start in recording seconds. Notes that begin
    before the interval or inside either boundary margin are excluded.
    """
    if duration <= 2 * margin or margin < 0:
        raise ValueError('duration must be longer than twice the margin')
    with sqlite3.connect(f'file:{database.resolve()}?mode=ro', uri=True) as conn:
        rows = conn.execute(
            'SELECT onset, pitch, duration FROM melody WHERE melid=? ORDER BY onset',
            (melid,),
        ).fetchall()
    if not rows:
        raise ValueError(f'No Weimar notes for melid {melid}')
    result = []
    for onset, pitch, length in rows:
        start = onset + reference_zero - crop_start
        if margin <= start < duration - margin and length > 0:
            result.append((start, start + length, int(pitch), 100))
    return result


def reading_events(score, tempo: float, origin: float):
    """Map reading-copy notation to clip seconds; merge ties and ignore chords.

    This assumes a constant tempo and straight playback. It evaluates the
    notation approximation, not the raw detector output.
    """
    import music21

    if tempo <= 0:
        raise ValueError('tempo must be positive')
    part = score.parts[0].stripTies(inPlace=False)
    events = []
    for note in part.recurse().getElementsByClass(music21.note.Note):
        start = float(note.getOffsetInHierarchy(part)) * 60 / tempo + origin
        end = start + float(note.quarterLength) * 60 / tempo
        events.append((start, end, note.pitch.midi, 100))
    return sorted(events)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('database', type=Path)
    p.add_argument('midi', type=Path)
    p.add_argument('--melid', type=int, required=True)
    p.add_argument('--reference-zero', type=float, required=True)
    p.add_argument('--crop-start', type=float, required=True)
    p.add_argument('--duration', type=float, required=True)
    p.add_argument('--margin', type=float, default=0.25)
    p.add_argument('--onset-tolerance', type=float, default=0.05)
    p.add_argument('--score-tempo', type=float, help='required for MusicXML')
    p.add_argument('--score-origin', type=float, help='required for MusicXML')
    args = p.parse_args()
    reference = reference_excerpt(args.database, args.melid, args.reference_zero,
                                  args.crop_start, args.duration, args.margin)
    if not reference:
        raise ValueError('No reference notes in selected excerpt')
    if args.midi.suffix.lower() in ('.musicxml', '.xml'):
        if args.score_tempo is None or args.score_origin is None:
            p.error('MusicXML requires --score-tempo and --score-origin')
        import music21
        candidates = reading_events(music21.converter.parse(args.midi),
                                    args.score_tempo, args.score_origin)
    else:
        candidates = load_midi(args.midi)
    estimate = [n for n in candidates
                if args.margin <= n[0] < args.duration - args.margin]
    result = TranscriptionEvaluator(args.onset_tolerance).evaluate(estimate, reference)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
