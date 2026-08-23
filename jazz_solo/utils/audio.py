"""Audio I/O and processing utilities."""

import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import soundfile as sf
import torch
import torchaudio

logger = logging.getLogger(__name__)


def load_audio(
    path: str | Path,
    target_sr: int = 22050,
    mono: bool = True,
) -> Tuple[np.ndarray, int]:
    """Load audio from disk, resample to *target_sr*, optionally convert to mono.

    Returns
    -------
    audio : np.ndarray, shape (samples,) or (channels, samples)
    sr : int
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    try:
        audio, orig_sr = sf.read(str(path))
    except Exception:
        logger.info(f"soundfile failed on {path}, trying torchaudio…")
        waveform, orig_sr = torchaudio.load(str(path))
        audio = waveform.numpy()

    # Convert to mono by averaging channels
    if mono and audio.ndim > 1:
        audio = audio.mean(axis=0)

    # Resample if needed
    if orig_sr != target_sr:
        audio_t = torch.from_numpy(audio).float()[None, :]  # [1, samples]
        resampled = torchaudio.functional.resample(
            audio_t, orig_sr, target_sr
        )
        audio = resampled[0].numpy()

    return audio, target_sr


def save_audio(
    path: str | Path,
    audio: np.ndarray,
    sr: int,
    normalize: bool = True,
) -> Path:
    """Write a numpy array to a WAV file.

    If *normalize* is True, the signal is peak-normalised to [-1, 1].
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if normalize and np.abs(audio).max() > 0:
        audio = audio / np.abs(audio).max()

    sf.write(str(path), audio, sr)
    return path


def spectrogram(
    audio: np.ndarray,
    sr: int = 22050,
    n_fft: int = 2048,
    hop_length: int = 512,
    n_mels: int = 128,
    log: bool = True,
) -> np.ndarray:
    """Compute a log-mel spectrogram from raw audio.

    Returns
    -------
    S : np.ndarray, shape (n_mels, time_frames)
    """
    import librosa

    mel = librosa.feature.melspectrogram(
        y=audio, sr=sr, n_fft=n_fft, hop_length=hop_length, n_mels=n_mels
    )
    if log:
        mel = librosa.power_to_db(mel, ref=np.max)
    return mel


def trim_silence(
    audio: np.ndarray,
    top_db: float = 30,
    frame_length: int = 2048,
    hop_length: int = 512,
) -> np.ndarray:
    """Trim leading / trailing silence from an audio signal."""
    import librosa

    trimmed, _ = librosa.effects.trim(
        audio, top_db=top_db, frame_length=frame_length, hop_length=hop_length
    )
    return trimmed