"""MIDI utilities — reading, writing, converting note events."""

import logging
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pretty_midi

logger = logging.getLogger(__name__)

# ── data structures ──────────────────────────────────────────────────

NoteEvent = Tuple[float, float, int, float]
"""A single note: (start_time_sec, end_time_sec, pitch_midi, velocity)."""


# ── note-event helpers ──────────────────────────────────────────────


def notes_to_pretty_midi(
    notes: List[NoteEvent],
    tempo: float = 120.0,
    program: int = 66,  # tenor sax
) -> pretty_midi.PrettyMIDI:
    """Convert a list of (start, end, pitch, velocity) tuples to a PrettyMIDI object."""
    pm = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    instrument = pretty_midi.Instrument(program=program)

    for start, end, pitch, vel in notes:
        note = pretty_midi.Note(
            velocity=int(min(127, max(0, vel))),
            pitch=int(min(127, max(0, pitch))),
            start=float(start),
            end=float(end),
        )
        instrument.notes.append(note)

    pm.instruments.append(instrument)
    return pm


def save_midi(
    notes: List[NoteEvent],
    output_path: str | Path,
    tempo: float = 120.0,
    program: int = 66,
) -> Path:
    """Write notes to a MIDI file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pm = notes_to_pretty_midi(notes, tempo=tempo, program=program)
    pm.write(str(output_path))
    logger.info(f"Saved MIDI → {output_path}")
    return output_path


def load_midi(path: str | Path) -> List[NoteEvent]:
    """Load notes from a MIDI file."""
    pm = pretty_midi.PrettyMIDI(str(path))
    notes: List[NoteEvent] = []
    for instrument in pm.instruments:
        for note in instrument.notes:
            notes.append((note.start, note.end, note.pitch, note.velocity))
    return sorted(notes, key=lambda x: x[0])


def notes_to_music21_stream(
    notes: List[NoteEvent],
    quantized: bool = False,
) -> "music21.stream.Part":  # noqa: F821
    """Convert note events to a music21 stream for score export / analysis."""
    import music21

    part = music21.stream.Part()
    for start, end, pitch, vel in notes:
        dur = end - start
        n = music21.note.Note(pitch, quarterLength=dur if quantized else dur)
        n.volume.velocityScalar = vel / 127.0
        part.insert(start, n)
    return part


def export_musicxml(
    notes: List[NoteEvent],
    output_path: str | Path,
    quantized: bool = False,
) -> Path:
    """Export transcribed notes as MusicXML (useful for score editors)."""
    import music21

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stream = music21.stream.Score()
    part = notes_to_music21_stream(notes, quantized=quantized)
    stream.append(part)
    stream.write("musicxml", fp=str(output_path))
    logger.info(f"Saved MusicXML → {output_path}")
    return output_path


def trim_sustained_noise(
    notes: List[NoteEvent],
    max_vel_ratio: float = 0.4,
) -> List[NoteEvent]:
    """Filter out very quiet notes that are likely cymbal bleed / noise."""
    if not notes:
        return []
    max_vel = max(n[3] for n in notes)
    threshold = max_vel * max_vel_ratio
    return [n for n in notes if n[3] >= threshold]