"""Pipeline orchestrator — ties Stages A, B, and C into one end-to-end flow.

Usage::

    from jazz_solo.pipeline import JazzSoloPipeline

    pipeline = JazzSoloPipeline()
    notes = pipeline.transcribe("my_jazz_track.wav")
"""

import logging
from pathlib import Path
from typing import List, Optional

from jazz_solo.config import PipelineConfig
from jazz_solo.pipeline.separator import AudioSeparator
from jazz_solo.pipeline.transcriber import NoteTranscriber
from jazz_solo.pipeline.quantizer import RhythmicQuantizer
from jazz_solo.utils.audio import load_audio
from jazz_solo.utils.midi import NoteEvent, save_midi, export_musicxml

logger = logging.getLogger(__name__)


class JazzSoloPipeline:
    """End-to-end jazz solo transcription pipeline.

    Transforms a raw jazz recording → isolated solo → MIDI notes →
    rhythmically quantized score.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.separator = AudioSeparator(self.config.separator)
        self.transcriber = NoteTranscriber(self.config.transcriber)
        self.quantizer = RhythmicQuantizer(self.config.quantizer)

    def transcribe(
        self,
        input_path: str | Path,
        output_dir: Optional[str | Path] = None,
        skip_separation: Optional[bool] = None,
    ) -> List[NoteEvent]:
        """Run the full pipeline on a jazz track.

        Parameters
        ----------
        input_path : str | Path
            Path to the input jazz recording (any format supported by ffmpeg).
        output_dir : str | Path | None
            Output directory for stems, MIDI, MusicXML.
            Defaults to ``<input_stem>_transcription/``.
        skip_separation : bool | None
            If True, treat the input as already an isolated solo track.
            Defaults to ``config.skip_separation``.

        Returns
        -------
        list[NoteEvent]
            Quantized note events: (start_sec, end_sec, midi_pitch, velocity).
        """
        input_path = Path(input_path)
        skip_sep = (
            skip_separation if skip_separation is not None
            else self.config.skip_separation
        )

        if output_dir is None:
            output_dir = input_path.parent / f"{input_path.stem}_transcription"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # ── Stage A: Source Separation ──────────────────────────
        if not skip_sep:
            solo_path = self.separator.separate(input_path, output_dir=output_dir)
        else:
            solo_path = input_path
            logger.info("[Pipeline] Skipping source separation (input is solo)")

        # ── Stage B: Note transcription ─────────────────────────
        midi_raw_path = output_dir / "01_raw_transcription.mid"
        notes = self.transcriber.transcribe(
            solo_path, output_midi=midi_raw_path
        )

        if not notes:
            logger.warning("[Pipeline] No notes detected in the solo")
            return []

        # ── Stage C: Rhythmic quantization ──────────────────────
        # Use the original audio (full mix) for beat tracking
        beat_track_source = input_path if not skip_sep else solo_path
        quantized_notes = self.quantizer.align(notes, beat_track_source)

        # ── Write outputs ───────────────────────────────────────
        midi_quantized_path = output_dir / "02_quantized_transcription.mid"
        save_midi(quantized_notes, midi_quantized_path, tempo=120.0)

        musicxml_path = output_dir / "03_transcription.musicxml"
        try:
            export_musicxml(quantized_notes, musicxml_path, quantized=True)
        except Exception as e:
            logger.warning(f"MusicXML export failed (non-fatal): {e}")

        if self.config.verbose:
            self._log_summary(input_path, output_dir, notes, quantized_notes)

        return quantized_notes

    def _log_summary(
        self,
        input_path: Path,
        output_dir: Path,
        raw: List[NoteEvent],
        quantized: List[NoteEvent],
    ) -> None:
        """Log a human-readable summary of the transcription results."""
        input_dur = 0.0
        if raw:
            input_dur = raw[-1][1] - raw[0][0]

        pitches = set(n[2] for n in quantized)
        logger.info("=" * 50)
        logger.info(f"Transcription complete: {input_path.name}")
        logger.info(f"  Output directory:  {output_dir}")
        logger.info(f"  Track duration:    {input_dur:.1f}s")
        logger.info(f"  Raw note events:   {len(raw)}")
        logger.info(f"  Quantized notes:   {len(quantized)}")
        logger.info(f"  Pitch range:       {min(pitches)}–{max(pitches)} MIDI")
        logger.info(f"  Note density:      {len(quantized) / max(input_dur, 0.1):.1f} notes/sec")
        logger.info("=" * 50)