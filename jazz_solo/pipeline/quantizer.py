"""Stage C: Metrical alignment & quantization.

Jazz soloists play with expressive microtiming — laying back on the beat,
rushing through passages, swinging.  This stage takes raw milliseconds from
the transcriber and snaps them to a musically meaningful grid.

The pipeline:
1. Beat tracking (madmom) — locate downbeats and quarter-note positions
2. Tempo estimation — derive the underlying pulse
3. Swing detection — measure the swing ratio from eighth-note pairs
4. Quantization — snap note onsets/offsets to the nearest grid position
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from jazz_solo.config import QuantizerConfig
from jazz_solo.utils.midi import NoteEvent, notes_to_pretty_midi, save_midi

logger = logging.getLogger(__name__)


@dataclass
class BeatMap:
    """The metrical structure of a track."""

    beats: np.ndarray
    """Beat positions in seconds (every quarter-note pulse)."""
    downbeats: np.ndarray
    """Downbeat (bar-line) positions in seconds."""
    tempo: float
    """Estimated tempo in BPM."""
    swing_ratio: float
    """Swing ratio (0.0 = straight, ~0.67 = typical swing)."""
    time_signature: str
    """Detected or assumed time signature."""


class RhythmicQuantizer:
    """Quantize raw MIDI notes to a musical grid."""

    def __init__(self, config: Optional[QuantizerConfig] = None):
        self.config = config or QuantizerConfig()

    def align(self, notes: List[NoteEvent], audio_path: str | Path) -> List[NoteEvent]:
        """Full metrical alignment pipeline.

        1. Beat-track the original audio to build a *BeatMap*.
        2. Quantize all note onsets and offsets to the nearest grid position.

        Parameters
        ----------
        notes : list[NoteEvent]
            Raw un-quantized notes from Stage B.
        audio_path : str | Path
            **Original** full mix or isolated track used for beat tracking.

        Returns
        -------
        list[NoteEvent]
            Quantized notes with metrically-aligned timings.
        """
        beat_map = self._build_beat_map(audio_path)

        if self.config.swing_ratio == 0.0:
            beat_map.swing_ratio = beat_map.swing_ratio or 0.0
            if beat_map.swing_ratio < 0.01:
                logger.info("[Stage C] No swing detected, using straight grid")
        else:
            beat_map.swing_ratio = self.config.swing_ratio

        logger.info(
            f"[Stage C] Tempo: {beat_map.tempo:.1f} BPM | "
            f"Swing: {beat_map.swing_ratio:.3f} | "
            f"Time signature: {beat_map.time_signature}"
        )

        quantized = self._quantize_notes(notes, beat_map)
        logger.info(
            f"[Stage C] Quantized {len(notes)} → {len(quantized)} notes"
        )
        return quantized

    # ── Beat tracking ───────────────────────────────────────────

    def _build_beat_map(self, audio_path: str | Path) -> BeatMap:
        """Build a metrical map of the track using madmom."""
        logger.info("[Stage C] Running beat tracking …")

        if self.config.model == "madmom":
            return self._beat_track_madmom(audio_path)
        else:
            return self._beat_track_librosa(audio_path)

    def _beat_track_madmom(self, audio_path: str | Path) -> BeatMap:
        """madmom-based beat + downbeat tracking.

        madmom's RNNDownBeatProcessor gives beat + downbeat positions.
        """
        try:
            import madmom
            from madmom.features.beats import (
                DBNBeatTrackingProcessor,
                RNNBeatProcessor,
            )
            from madmom.features.downbeats import (
                DBNDownBeatTrackingProcessor,
                RNNDownBeatProcessor,
            )
        except ImportError:
            logger.warning(
                "madmom not fully installed; falling back to librosa"
            )
            return self._beat_track_librosa(audio_path)

        # Load audio via madmom's signal processor
        sig_proc = madmom.audio.SignalProcessor(
            num_channels=1, sample_rate=44100
        )
        frames = madmom.audio.FrameProcessor(
            sig_proc(audio_path), frame_size=2048, hop_size=441
        )

        # Beat tracking
        act_proc = RNNBeatProcessor()(frames)
        beats = DBNBeatTrackingProcessor(
            min_bpm=self.config.min_bpm,
            max_bpm=self.config.max_bpm,
        )(act_proc)

        # Downbeat tracking
        dbn_proc = RNNDownBeatProcessor()(frames)
        beats_db = DBNDownBeatTrackingProcessor(
            beats_per_bar=[3, 4],
            min_bpm=self.config.min_bpm,
            max_bpm=self.config.max_bpm,
        )(dbn_proc)

        downbeats = beats_db[beats_db[:, 1] == 1][:, 0]

        tempo = float(np.mean(60.0 / np.diff(beats))) if len(beats) > 1 else 120.0

        swing = self._detect_swing(audio_path, beats)

        ts = "3/4" if len(downbeats) > 1 and np.median(
            np.diff(downbeats) / np.median(np.diff(beats))
        ) < 3.5 else "4/4"

        return BeatMap(
            beats=np.array(beats),
            downbeats=np.array(downbeats),
            tempo=tempo,
            swing_ratio=swing,
            time_signature=ts,
        )

    def _beat_track_librosa(self, audio_path: str | Path) -> BeatMap:
        """librosa-based fallback beat tracking."""
        import librosa

        y, sr = librosa.load(str(audio_path), sr=None, mono=True)

        tempo, beats = librosa.beat.beat_track(
            y=y, sr=sr,
            units="time",
            bpm=(self.config.min_bpm, self.config.max_bpm),
        )

        # Very rough downbeat detection: assume first beat = downbeat
        if isinstance(tempo, np.ndarray):
            tempo = float(tempo[0]) if len(tempo) > 0 else 120.0
        tempo = float(tempo)

        downbeats = beats[::4]  # assume 4/4

        swing = self._detect_swing_from_beats(audio_path, beats)

        return BeatMap(
            beats=beats,
            downbeats=downbeats,
            tempo=tempo,
            swing_ratio=swing,
            time_signature="4/4",
        )

    # ── Swing detection ─────────────────────────────────────────

    def _detect_swing(
        self, audio_path: str | Path, beats: np.ndarray
    ) -> float:
        """Analyse inter-beat intervals for swing feel.

        Swing = ratio of the longer eighth-note to the quarter-note.
        Straight = 0.33 (1:1), heavy swing ≈ 0.67 (2:1 triplet feel).
        """
        try:
            return self._detect_swing_from_beats(audio_path, beats)
        except Exception:
            return 0.0

    def _detect_swing_from_beats(
        self, audio_path: str | Path, beats: np.ndarray
    ) -> float:
        """Measure swing by looking at the ratio of C1 to C2 within each beat pair."""
        import librosa

        y, sr = librosa.load(str(audio_path), sr=None, mono=True)

        if len(beats) < 4:
            return 0.0

        # Get onset strength envelope
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)

        # For each pair of adjacent beats, find the strongest internal subdivision
        sub_ratios = []
        for i in range(len(beats) - 1):
            b1, b2 = beats[i], beats[i + 1]
            midpoint = (b1 + b2) / 2.0
            # Look for an inter-onset that's offset from the exact middle
            # — this is the swing feel
            quarter = (b2 - b1) / 2.0

            # Samples around the two potential 8th-note positions
            times = np.array([b1, b1 + quarter, b2])
            frames = librosa.time_to_frames(times, sr=sr)

            if len(frames) < 3:
                continue

            # Ratio of the second 8th-note offset
            c1 = onset_env[min(frames[1], len(onset_env) - 1)]
            c2 = onset_env[min(frames[2] - 1, len(onset_env) - 1)]

            denom = c1 + c2
            if denom > 0:
                sub_ratios.append(c2 / denom)

        if not sub_ratios:
            return 0.0

        # Remove outliers
        arr = np.array(sub_ratios)
        arr = arr[(arr > 0.1) & (arr < 0.9)]
        return float(np.median(arr)) if len(arr) > 0 else 0.0

    # ── Quantization ────────────────────────────────────────────

    def _quantize_notes(
        self, notes: List[NoteEvent], beat_map: BeatMap
    ) -> List[NoteEvent]:
        """Snap note events to the nearest grid subdivision."""
        if len(notes) == 0:
            return []

        grid = self._build_grid(beat_map)
        if len(grid) < 2:
            logger.warning("[Stage C] Grid too short; returning raw notes")
            return notes

        quantized: List[NoteEvent] = []
        for start, end, pitch, vel in notes:
            q_start = self._snap_to_grid(start, grid, beat_map)
            q_end = self._snap_to_grid(end, grid, beat_map)

            # Preserve minimum note length after quantization
            if q_end - q_start < 0.01:
                q_end = q_start + np.min(np.diff(grid))

            quantized.append((q_start, q_end, pitch, vel))

        # Remove duplicate notes (same pitch starting at same quantized time)
        deduped = self._deduplicate(quantized)
        return sorted(deduped, key=lambda x: x[0])

    def _build_grid(self, beat_map: BeatMap) -> np.ndarray:
        """Build a rhythmic grid from the beat map at the configured resolution."""
        if len(beat_map.beats) < 2:
            return beat_map.beats

        # Subdivisions per quarter note
        resolution_map = {
            "8th": 2,
            "16th": 4,
            "triplet_8th": 3,
            "triplet_16th": 6,
        }
        subdivs = resolution_map.get(self.config.grid_resolution, 4)

        grid_parts = []
        for i in range(len(beat_map.beats) - 1):
            b1, b2 = beat_map.beats[i], beat_map.beats[i + 1]
            beat_dur = b2 - b1

            for s in range(subdivs):
                t = b1 + (s / subdivs) * beat_dur
                # Apply swing offset for non-straight 8ths
                if subdivs in (2, 4) and s % 2 == 1 and beat_map.swing_ratio > 0.01:
                    swing_shift = beat_dur * (beat_map.swing_ratio - 0.5)
                    # Clamp so swung notes don't cross the next beat
                    swing_shift = max(-beat_dur * 0.4, min(beat_dur * 0.4, swing_shift))
                    t += swing_shift
                grid_parts.append(t)

        grid_parts.append(beat_map.beats[-1])
        return np.array(sorted(set(grid_parts)))

    def _snap_to_grid(self, time: float, grid: np.ndarray, beat_map: BeatMap) -> float:
        """Snap a time value to the nearest grid position."""
        idx = np.argmin(np.abs(grid - time))
        snapped = grid[idx]

        # Only snap if within a reasonable tolerance (quarter-note)
        max_snap = 60.0 / beat_map.tempo if beat_map.tempo > 0 else 0.5
        if abs(snapped - time) > max_snap:
            return time  # don't snap really far-off notes
        return snapped

    def _deduplicate(self, notes: List[NoteEvent]) -> List[NoteEvent]:
        """Remove overlapping notes of the same pitch (pick loudest)."""
        if not notes:
            return []

        sorted_notes = sorted(notes, key=lambda x: (x[2], x[0]))
        result = [sorted_notes[0]]

        for note in sorted_notes[1:]:
            last = result[-1]
            if (
                note[0] == last[0]
                and note[1] == last[1]
                and note[2] == last[2]
            ):
                # Identical time+pitch — keep louder
                if note[3] > last[3]:
                    result[-1] = note
            elif (
                note[2] == last[2]
                and note[0] < last[1]
            ):
                # Same pitch, overlapping — merge
                merged_end = max(last[1], note[1])
                merged_vel = max(last[3], note[3])
                result[-1] = (last[0], merged_end, last[2], merged_vel)
            else:
                result.append(note)

        return result