"""Export explicitly supplied Weimar chord annotations for a reading copy.

This is reference-assisted context, not automatic chord recognition. The caller
must verify the recording, take and reference alignment.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

import music21


def convert_chord(label: str) -> str:
    """Translate common Weimar chord spellings into MusicXML lead-sheet figures."""
    if label == 'NC':
        return 'N.C.'
    match = re.fullmatch(r'([A-G][b#]?)(.*)', label)
    if not match:
        raise ValueError(f'Unsupported Weimar chord: {label!r}')
    root, suffix = match.groups()
    root = root.replace("b", "-")
    if suffix.startswith('-'):
        suffix = 'm' + suffix[1:]
    elif suffix.startswith('j'):
        suffix = 'maj' + suffix[1:]
    figure = root + suffix
    try:
        music21.harmony.ChordSymbol(figure)
    except Exception as exc:
        raise ValueError(f'Unsupported Weimar chord: {label!r}') from exc
    return figure


def extract_chords(database: Path, melid: int, reference_zero: float,
                   crop_start: float, score_start: float, duration: float):
    """Return reference chord changes in clip seconds, including carried harmony."""
    if duration <= score_start:
        raise ValueError('duration must be later than score start')
    with sqlite3.connect(f'file:{database.resolve()}?mode=ro', uri=True) as conn:
        rows = conn.execute(
            "SELECT onset, chord FROM beats WHERE melid=? AND chord<>'' ORDER BY onset",
            (melid,),
        ).fetchall()
    if not rows:
        raise ValueError(f'No annotated harmony for melid {melid}')
    changes = [(onset + reference_zero - crop_start, label) for onset, label in rows]
    preceding = [label for time, label in changes if time < score_start]
    result = []
    if preceding:
        result.append({'time': score_start, 'symbol': convert_chord(preceding[-1])})
    for time, label in changes:
        if score_start <= time < duration:
            result.append({'time': round(time, 6), 'symbol': convert_chord(label)})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--melid', type=int, required=True)
    parser.add_argument('--reference-zero', type=float, required=True)
    parser.add_argument('--crop-start', type=float, required=True)
    parser.add_argument('--score-start', type=float, default=0)
    parser.add_argument('--duration', type=float, required=True)
    args = parser.parse_args()
    chords = extract_chords(args.database, args.melid, args.reference_zero,
                            args.crop_start, args.score_start, args.duration)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(chords, indent=2) + '\n')


if __name__ == '__main__':
    main()
