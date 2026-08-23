"""Stage B: Pitch and onset detection.

Transforms isolated soloist audio into symbolic note events (MIDI).
Supports two backends:

- **basic-pitch** (default) — Spotify's CNN-based model, fast, great for
  monophonic / homophonic instruments (sax, trumpet, piano comping).
- **mt3** — Google's MT3 Transformer, polyphonic, higher accuracy on dense
  passages, requires more compute.
"""

import logging
from pathlib import Path
from typing import List, Optional

import numpy as np

from jazz_solo.config import TranscriberConfig
from jazz_solo.utils.midi import NoteEvent, notes_to_pretty_midi

logger = logging.getLogger(__name__)


class NoteTranscriber:
    """Convert isolated solo audio to note events."""

    def __init__(self, config: Optional[TranscriberConfig] = None):
        self.config = config or TranscriberConfig()

    def transcribe(
        self,
        audio_path: str | Path,
        output_midi: Optional[str | Path] = None,
    ) -> List[NoteEvent]:
        """Transcribe an audio file to note events.

        Parameters
        ----------
        audio_path : str | Path
            Path to the isolated solo audio (WAV preferred).
        output_midi : str | Path | None
            Optional path to write a MIDI file.

        Returns
        -------
        list[NoteEvent]
            List of (start_sec, end_sec, midi_pitch, velocity) tuples.
        """
        if self.config.model == "basic-pitch":
            return self._transcribe_basic_pitch(audio_path, output_midi)
        elif self.config.model == "mt3":
            return self._transcribe_mt3(audio_path, output_midi)
        else:
            raise ValueError(
                f"Unknown transcriber model: {self.config.model}. "
                "Choose 'basic-pitch' or 'mt3'."
            )

    # ── Basic Pitch backend ──────────────────────────────────────────

    def _transcribe_basic_pitch(
        self,
        audio_path: str | Path,
        output_midi: Optional[str | Path] = None,
    ) -> List[NoteEvent]:
        """Use Spotify's Basic Pitch for fast monophonic/homophonic transcription."""
        logger.info("[Stage B] Transcribing with Basic Pitch …")

        import basic_pitch
        from basic_pitch import ICASSP_2022_MODEL_PATH
        import tensorflow as tf

        model = tf.saved_model.load(ICASSP_2022_MODEL_PATH)

        model_output, midi_data, note_events = basic_pitch.infer(
            model,
            str(audio_path),
            onset_threshold=self.config.onset_threshold,
            frame_threshold=self.config.frame_threshold,
            minimum_note_length=self.config.minimum_note_length,
        )

        notes: List[NoteEvent] = []
        for start, end, pitch, velocity in note_events:
            if (end - start) >= self.config.minimum_note_length:
                notes.append((float(start), float(end), int(pitch), int(velocity)))

        # Trim absurdly long notes
        notes = [
            n for n in notes
            if (n[1] - n[0]) <= self.config.maximum_note_length
        ]

        logger.info(f"[Stage B] Detected {len(notes)} note events")

        if output_midi:
            midi_data.write(str(output_midi))
            logger.info(f"[Stage B] MIDI written → {output_midi}")

        return notes

    # ── MT3 backend ──────────────────────────────────────────────────

    def _transcribe_mt3(
        self,
        audio_path: str | Path,
        output_midi: Optional[str | Path] = None,
    ) -> List[NoteEvent]:
        """Use a pre-trained MT3 model for polyphonic transcription.

        Requires ``mt3`` and ``t5`` packages installed separately.
        """
        logger.info("[Stage B] Transcribing with MT3 …")

        try:
            import soundfile as sf
            import gin
            import mt3
            import t5
        except ImportError:
            raise ImportError(
                "MT3 requires 'mt3', 'gin-config', and 't5' packages.\n"
                "Install with: pip install git+https://github.com/magenta/mt3.git"
            )

        # ── MT3 inference ────────────────────────────────────────
        # This follows the mt3 colab inference pattern.
        # We load a pre-trained checkpoint from HuggingFace / GCS.
        audio, sr = sf.read(str(audio_path))
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        # The actual MT3 inference call depends on the checkpoint format.
        # We provide the scaffolding — users point to their checkpoint.
        # TODO: wire up MT3 checkpoint loading when checkpoint path is configured.

        raise NotImplementedError(
            "MT3 inference requires a pre-trained checkpoint. "
            "See scripts/download_mt3_checkpoint.sh for setup, "
            "or switch to basic-pitch model."
        )

    def transcribe_notes_only(
        self, audio: np.ndarray, sr: int
    ) -> List[NoteEvent]:
        """Programmatic transcribe from a numpy array (no filesystem).

        Writes a temporary WAV and runs the configured backend.
        """
        import tempfile
        import soundfile as sf

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, audio, sr)
            tmp_path = tmp.name

        try:
            return self.transcribe(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)