"""Global configuration for the jazz solo transcriber pipeline."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SeparatorConfig:
    """Settings for Demucs-based source separation (Stage A)."""
    model: str = "htdemucs"
    """Demucs model variant: 'htdemucs' (best quality) or 'htdemucs_ft' (fine-tuned)."""
    shifts: int = 1
    """Number of random shifts for test-time equivariance (1=fast, 5=best quality)."""
    overlap: float = 0.25
    """Overlap between prediction windows."""
    stem: str = "other"
    """Target stem to extract: 'vocals', 'drums', 'bass', 'other', or 'all'."""
    device: str = "cpu"
    """Compute device: 'cpu', 'cuda', or 'mps'."""
    segment: int = 20
    """Segment length in seconds for Demucs processing."""


@dataclass
class TranscriberConfig:
    """Settings for pitch/onset transcription (Stage B)."""
    model: str = "basic-pitch"
    """Backend: 'basic-pitch' (fast, monophonic) or 'mt3' (polyphonic, slower)."""
    onset_threshold: float = 0.5
    """Minimum onset activation to register a note start."""
    frame_threshold: float = 0.3
    """Minimum frame activation to sustain a note."""
    minimum_note_length: float = 0.058
    """Shortest allowable note in seconds (≈32nd note at 120 BPM)."""
    maximum_note_length: float = 4.0
    """Longest allowable note in seconds."""
    melodia_activations: bool = True
    """Use CREPE/Melodia activations for pitch refinement when available."""
    device: str = "cpu"


@dataclass
class QuantizerConfig:
    """Settings for metrical alignment and quantization (Stage C)."""
    model: str = "madmom"
    """Rhythm backend: 'madmom' or 'librosa'."""
    min_bpm: float = 40.0
    """Minimum plausible tempo in BPM."""
    max_bpm: float = 400.0
    """Maximum plausible tempo in BPM."""
    swing_ratio: float = 0.0
    """Swing factor (0.0=straight, 0.5=heavy swing). Auto-detected when 0.0."""
    time_signature: str = "auto"
    """Time signature: '4/4', '3/4', or 'auto' for detection."""
    grid_resolution: str = "16th"
    """Smallest note value: '8th', '16th', 'triplet_8th', 'triplet_16th'."""


@dataclass
class PipelineConfig:
    """Complete pipeline configuration."""
    separator: SeparatorConfig = field(default_factory=SeparatorConfig)
    transcriber: TranscriberConfig = field(default_factory=TranscriberConfig)
    quantizer: QuantizerConfig = field(default_factory=QuantizerConfig)
    sample_rate: int = 22050
    """Target sample rate for processing."""
    output_dir: str = "jazz_transcriptions"
    """Directory for transcription outputs."""
    skip_separation: bool = False
    """Skip source separation if the input is already an isolated track."""
    save_stems: bool = True
    """Save isolated stems alongside the transcription."""
    verbose: bool = True