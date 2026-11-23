"""Compare a local GuitarSet JAMS annotation and audio-aligned MIDI.

GuitarSet recordings/annotations must be obtained separately from the dataset.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from jazz_solo.training.evaluate import TranscriptionEvaluator
from jazz_solo.utils.midi import load_midi


def guitarset_reference(path: Path):
    """Read the per-string note_midi annotations in a GuitarSet JAMS file."""
    data = json.loads(path.read_text())
    notes = []
    for annotation in data['annotations']:
        if annotation.get('namespace') != 'note_midi':
            continue
        for event in annotation['data']:
            start = float(event['time'])
            duration = float(event['duration'])
            if duration > 0 and start >= 0:
                notes.append((start, start + duration, round(event['value']), 100))
    if not notes:
        raise ValueError(f'No GuitarSet note_midi events in {path}')
    return sorted(notes)


def evaluate_guitarset(estimated, reference, min_velocity=0, pitch_range=None,
                       onset_tolerance=.05):
    """Evaluate onset/pitch matches; note offsets are not scored."""
    if not 0 <= min_velocity <= 127:
        raise ValueError('min_velocity must be between 0 and 127')
    if pitch_range is not None and not 0 <= pitch_range[0] <= pitch_range[1] <= 127:
        raise ValueError('pitch_range must be ascending MIDI pitches')
    selected = [n for n in estimated if n[3] >= min_velocity and
                (pitch_range is None or pitch_range[0] <= n[2] <= pitch_range[1])]
    return TranscriptionEvaluator(onset_tolerance).evaluate(selected, reference)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('annotation', type=Path)
    parser.add_argument('midi', type=Path)
    parser.add_argument('--min-velocity', type=int, default=0)
    parser.add_argument('--pitch-range', type=int, nargs=2, default=None)
    parser.add_argument('--onset-tolerance', type=float, default=.05)
    args = parser.parse_args()
    result = evaluate_guitarset(load_midi(args.midi), guitarset_reference(args.annotation),
                                args.min_velocity, args.pitch_range, args.onset_tolerance)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
