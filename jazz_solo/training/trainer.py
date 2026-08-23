"""Fine-tuning harness for the jazz solo transcriber.

Provides training loops for fine-tuning Basic Pitch or MT3 on jazz data.

Basic Pitch fine-tuning approach:
  - Freeze the CNN frontend
  - Fine-tune the fully-connected layers on Weimar Jazz Database spectrograms
  - Loss = binary cross-entropy onset loss + frame activation loss

MT3 fine-tuning approach:
  - Load pre-trained T5-small checkpoint
  - Fine-tune on Weimar token sequences (spectrogram → MIDI-like tokens)
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Hyperparameters and paths for fine-tuning."""

    # Data
    dataset_path: str = ""  # Path to preprocessed NPZ file
    val_split: float = 0.1
    batch_size: int = 8
    num_epochs: int = 50
    learning_rate: float = 1e-4
    weight_decay: float = 1e-5

    # Checkpointing
    output_dir: str = "training_output"
    save_every: int = 5
    resume_from: Optional[str] = None

    # Transcribe base
    model_type: str = "basic-pitch"  # "basic-pitch" or "mt3"
    freeze_backbone: bool = True

    # Augmentation
    pitch_shift_range: int = 2  # semitones
    time_stretch_range: float = 0.1  # 10% max

    # Logging
    log_every: int = 10
    use_wandb: bool = False


class BasicPitchFineTuner:
    """Fine-tune Spotify's Basic Pitch on jazz data.

    Basic Pitch uses a CNN → harmonic stacking → fully-connected architecture.
    We replace the final classifier layers and train on Weimar note labels.
    """

    def __init__(self, config: TrainingConfig):
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.model = None
        self.optimizer = None

    def build_model(self) -> None:
        """Load pre-trained Basic Pitch, replace the head."""
        import tensorflow as tf
        from basic_pitch import ICASSP_2022_MODEL_PATH

        logger.info("Loading pre-trained Basic Pitch model…")
        self.model = tf.saved_model.load(ICASSP_2022_MODEL_PATH)

        if self.config.freeze_backbone:
            logger.info("Freezing backbone layers…")

    def train(self, train_data_path: str | Path) -> Dict[str, float]:
        """Run the fine-tuning loop.

        Parameters
        ----------
        train_data_path : str | Path
            Path to preprocessed NPZ file (from ``preprocess_weimar.py``).

        Returns
        -------
        dict
            Training metrics (loss, onset_f1, frame_f1).
        """
        logger.info("=" * 50)
        logger.info("Basic Pitch Fine-Tuning")
        logger.info(f"  Dataset: {train_data_path}")
        logger.info(f"  Epochs:  {self.config.num_epochs}")
        logger.info(f"  LR:      {self.config.learning_rate}")
        logger.info("=" * 50)

        self.build_model()

        # TODO: Full training loop
        # Requires: (1) data loader yields spectrogram→label pairs
        #           (2) custom onset loss + frame BCE loss
        #           (3) per-epoch eval with mir_eval metrics

        logger.warning(
            "Full training loop not yet wired — see TODO in code.\n"
            "Run `scripts/train.sh` after wiring data pipeline."
        )

        return {"loss": 0.0, "onset_f1": 0.0, "frame_f1": 0.0}


class MT3FineTuner:
    """Fine-tune Google's MT3 for polyphonic jazz transcription.

    MT3 is a T5-based encoder-decoder that treats transcription as
    a sequence-to-sequence problem: spectrogram patches → MIDI-like token
    sequences (NOTE_ON, NOTE_OFF, PITCH, etc.).
    """

    def __init__(self, config: TrainingConfig):
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def prepare(self) -> None:
        """Prepare the MT3 checkpoint and tokeniser."""
        logger.info("Preparing MT3 fine-tuning environment…")

        # MT3 expects:
        #   - Pre-trained T5 checkpoint (t5-base or t5-small)
        #   - Custom gin config overriding the output vocabulary to 512 MIDI tokens
        #   - Data in TFRecord format: spectrogram frames + token sequences

        # TODO: wire MT3 data preparation when the checkpoint is downloaded.
        # See: scripts/download_mt3_checkpoint.sh
        pass

    def train(self) -> Dict[str, float]:
        """Run MT3 fine-tuning.

        Returns
        -------
        dict
            Training metrics.
        """
        logger.info="MT3 fine-tuning requires: "
        "1) `scripts/download_mt3_checkpoint.sh` "
        "2) Weimar data preprocessed via `scripts/preprocess_weimar.py` "
        "3) A GPU instance (Lambda Labs / Modal)"
        return {"loss": 0.0, "onset_f1": 0.0, "note_f1": 0.0}