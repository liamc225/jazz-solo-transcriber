"""Stage A: Audio source separation via Demucs.

Takes a full jazz recording and isolates the soloist track by stripping
away drums, bass, and other accompaniment.
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np

from jazz_solo.config import SeparatorConfig
from jazz_solo.utils.audio import load_audio, save_audio

logger = logging.getLogger(__name__)


class AudioSeparator:
    """Isolate a soloist stem from a full mix using Demucs."""

    def __init__(self, config: Optional[SeparatorConfig] = None):
        self.config = config or SeparatorConfig()

    def separate(self, input_path: str | Path, output_dir: Optional[str | Path] = None) -> Path:
        """Run Demucs source separation and return the path to the isolated stem.

        Parameters
        ----------
        input_path : str | Path
            Path to the full mixed audio file.
        output_dir : str | Path | None
            Output directory.  Defaults to ``<input_stem>_stems/``.

        Returns
        -------
        Path
            Path to the isolated soloist WAV file.
        """
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Input audio not found: {input_path}")

        if output_dir is None:
            output_dir = input_path.parent / f"{input_path.stem}_stems"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"[Stage A] Separating stems with Demucs {self.config.model} …"
        )

        cmd = [
            "python3", "-m", "demucs",
            "--two-stems", self.config.stem,
            "-n", self.config.model,
            "--shifts", str(self.config.shifts),
            "--overlap", str(self.config.overlap),
            "-d", self.config.device,
            "--segment", str(self.config.segment),
            "-o", str(output_dir),
            str(input_path.resolve()),
        ]

        logger.debug(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600
        )

        if result.returncode != 0:
            logger.error(f"Demucs stderr:\n{result.stderr}")
            raise RuntimeError(
                f"Demucs separation failed (exit {result.returncode}): "
                f"{result.stderr[:500]}"
            )

        # Demucs output layout: output_dir / model_name / input_stem / {stem}.wav
        demucs_out = output_dir / self.config.model / input_path.stem
        stem_path = demucs_out / f"{self.config.stem}.wav"

        if not stem_path.exists():
            raise FileNotFoundError(
                f"Demucs completed but expected stem not found: {stem_path}\n"
                f"Available files: {list(demucs_out.iterdir())}"
            )

        logger.info(f"[Stage A] Isolated stem → {stem_path}")
        return stem_path

    def separate_raw(
        self, audio: np.ndarray, sr: int
    ) -> np.ndarray:
        """In-process separation (no filesystem) using temp files.

        Useful for programmatic use within a larger pipeline.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_in = Path(tmp) / "input.wav"
            save_audio(tmp_in, audio, sr)
            out_path = self.separate(tmp_in, output_dir=tmp)
            isolated, _ = load_audio(out_path, target_sr=sr)
        return isolated