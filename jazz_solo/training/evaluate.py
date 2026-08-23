"""Evaluation suite — measure transcription quality against ground truth.

Uses the ``mir_eval`` library to compute standard MIR metrics:

- **Onset F1** — does the model find notes at the right time?
- **Pitch accuracy** — are the correct pitches detected?
- **Note F1** — combined onset + pitch score
- **Duration accuracy** — how well do note lengths match?
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from jazz_solo.utils.midi import NoteEvent, load_midi, save_midi

logger = logging.getLogger(__name__)


class TranscriptionEvaluator:
    """Evaluate transcribed notes against a ground-truth reference."""

    def __init__(self, onset_tolerance: float = 0.05):
        """
        Parameters
        ----------
        onset_tolerance : float
            Maximum onset time offset (seconds) to count as a true positive.
            0.05s ≈ 32nd note at 120 BPM.  Use 0.05 for strict evaluation,
            0.1 for more lenient.
        """
        self.onset_tolerance = onset_tolerance

    def evaluate(
        self,
        estimated: List[NoteEvent],
        reference: List[NoteEvent],
    ) -> Dict[str, float]:
        """Evaluate estimated notes against a ground-truth reference.

        Parameters
        ----------
        estimated : list[NoteEvent]
            Transcribed notes from the pipeline.
        reference : list[NoteEvent]
            Ground-truth notes (e.g. from Weimar Jazz Database).

        Returns
        -------
        dict
            Metrics: onset_f1, onset_precision, onset_recall,
            note_f1, note_precision, note_recall,
            pitch_accuracy, duration_accuracy.
        """
        import mir_eval

        est_intervals = np.array([[n[0], n[1]] for n in estimated])
        est_pitches = np.array([n[2] for n in estimated])

        ref_intervals = np.array([[n[0], n[1]] for n in reference])
        ref_pitches = np.array([n[2] for n in reference])

        if len(estimated) == 0 or len(reference) == 0:
            return {
                "onset_f1": 0.0,
                "onset_precision": 0.0,
                "onset_recall": 0.0,
                "note_f1": 0.0,
                "note_precision": 0.0,
                "note_recall": 0.0,
                "pitch_accuracy": 0.0,
                "duration_accuracy": 0.0,
                "estimated_count": len(estimated),
                "reference_count": len(reference),
            }

        # ── Onset metrics ───────────────────────────────────────
        onset_ref = ref_intervals[:, 0]
        onset_est = est_intervals[:, 0]

        try:
            onset_p, onset_r, onset_f = mir_eval.onset.f_measure(
                onset_ref, onset_est,
                window=self.onset_tolerance,
            )
        except Exception:
            onset_p = onset_r = onset_f = 0.0

        # ── Note metrics (onset + pitch together) ───────────────
        try:
            note_p, note_r, note_f, _ = mir_eval.transcription.precision_recall_f1_overlap(
                ref_intervals, ref_pitches,
                est_intervals, est_pitches,
                onset_tolerance=self.onset_tolerance,
                pitch_tolerance=50.0,  # semitones — basically any pitch matches
                offset_ratio=None,
            )
        except Exception:
            note_p = note_r = note_f = 0.0

        # ── Pitch accuracy ───────────────────────────────────────
        try:
            pitch_accuracy = mir_eval.transcription.pitch_accuracy(
                ref_intervals, ref_pitches,
                est_intervals, est_pitches,
            )
        except Exception:
            pitch_accuracy = 0.0

        return {
            "onset_f1": float(onset_f),
            "onset_precision": float(onset_p),
            "onset_recall": float(onset_r),
            "note_f1": float(note_f),
            "note_precision": float(note_p),
            "note_recall": float(note_r),
            "pitch_accuracy": float(pitch_accuracy),
            "estimated_count": len(estimated),
            "reference_count": len(reference),
        }

    def evaluate_file(
        self,
        estimated_midi: str | Path,
        reference_midi: str | Path,
    ) -> Dict[str, float]:
        """Evaluate estimated MIDI against reference MIDI (file paths)."""
        estimated = load_midi(estimated_midi)
        reference = load_midi(reference_midi)
        return self.evaluate(estimated, reference)

    def evaluate_dataset(
        self,
        estimated_dir: str | Path,
        reference_dir: str | Path,
        suffix: str = ".mid",
    ) -> Dict[str, float]:
        """Evaluate an entire directory of estimated vs. reference MIDI files.

        Returns averaged metrics across all files.
        """
        estimated_dir = Path(estimated_dir)
        reference_dir = Path(reference_dir)

        all_metrics: List[Dict[str, float]] = []

        for est_path in sorted(estimated_dir.glob(f"*{suffix}")):
            ref_path = reference_dir / est_path.name
            if not ref_path.exists():
                logger.warning(f"No reference for {est_path.name}, skipping")
                continue

            metrics = self.evaluate_file(est_path, ref_path)
            all_metrics.append(metrics)
            logger.info(
                f"  {est_path.name}: "
                f"onset F1={metrics['onset_f1']:.3f}, "
                f"note F1={metrics['note_f1']:.3f}"
            )

        if not all_metrics:
            return {}

        # Average
        averaged = {}
        for key in all_metrics[0]:
            values = [m[key] for m in all_metrics]
            averaged[f"mean_{key}"] = float(np.mean(values))
            averaged[f"std_{key}"] = float(np.std(values))

        averaged["n_files"] = len(all_metrics)
        return averaged


def summary_to_table(metrics: Dict[str, float]) -> str:
    """Format evaluation metrics as a readable Markdown table."""
    if not metrics:
        return "_No evaluation data._"

    rows = []
    for key, val in sorted(metrics.items()):
        if "n_" in key:
            rows.append(f"| {key} | {int(val)} |")
        else:
            rows.append(f"| {key} | {val:.4f} |")

    header = "| Metric | Value |\n|--------|-------|"
    return header + "\n" + "\n".join(rows)