"""Tests for the jazz solo transcriber pipeline components."""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from jazz_solo.config import (
    PipelineConfig,
    SeparatorConfig,
    TranscriberConfig,
    QuantizerConfig,
)
from jazz_solo.utils.audio import load_audio, save_audio, spectrogram, trim_silence
from jazz_solo.utils.midi import (
    NoteEvent,
    notes_to_pretty_midi,
    save_midi,
    load_midi,
    export_musicxml,
    trim_sustained_noise,
)
from jazz_solo.pipeline.quantizer import BeatMap, RhythmicQuantizer


# ── Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def sample_audio() -> np.ndarray:
    """Generate a simple 440 Hz sine wave (1 second)."""
    sr = 22050
    t = np.linspace(0, 1.0, sr, endpoint=False)
    return 0.5 * np.sin(2 * np.pi * 440 * t)


@pytest.fixture
def sample_notes() -> list:
    """Simple scale: C4-E4-G4-C5."""
    return [
        (0.00, 0.25, 60, 100),   # C4
        (0.25, 0.50, 64, 100),   # E4
        (0.50, 0.75, 67, 100),   # G4
        (0.75, 1.00, 72, 100),   # C5
    ]


@pytest.fixture
def midi_file(tmp_path, sample_notes) -> Path:
    path = tmp_path / "test.mid"
    save_midi(sample_notes, path)
    return path


@pytest.fixture
def audio_file(tmp_path, sample_audio) -> Path:
    path = tmp_path / "test.wav"
    save_audio(path, sample_audio, sr=22050)
    return path


# ── Config tests ────────────────────────────────────────────────────────

class TestConfig:
    def test_default_config_creates(self):
        config = PipelineConfig()
        assert config.separator.model == "htdemucs"
        assert config.transcriber.model == "basic-pitch"
        assert config.quantizer.grid_resolution == "16th"
        assert config.sample_rate == 22050

    def test_separator_config_defaults(self):
        cfg = SeparatorConfig()
        assert cfg.stem == "other"
        assert cfg.device == "cpu"

    def test_transcriber_config_defaults(self):
        cfg = TranscriberConfig()
        assert cfg.onset_threshold == 0.5
        assert cfg.minimum_note_length == 0.058


# ── Audio utility tests ─────────────────────────────────────────────────

class TestAudioUtils:
    def test_save_and_load_audio(self, tmp_path, sample_audio):
        path = tmp_path / "test.wav"
        save_audio(path, sample_audio, sr=22050)
        assert path.exists()
        assert path.stat().st_size > 0

        loaded, sr = load_audio(path)
        assert sr == 22050
        assert len(loaded) > 0

    def test_load_audio_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            load_audio("/nonexistent/path.wav")

    def test_spectrogram_shape(self, sample_audio):
        spec = spectrogram(sample_audio, sr=22050, n_mels=128)
        assert spec.shape[0] == 128  # n_mels
        assert spec.shape[1] > 0     # time frames

    def test_spectrogram_log(self, sample_audio):
        spec_log = spectrogram(sample_audio, sr=22050, log=True)
        spec_lin = spectrogram(sample_audio, sr=22050, log=False)
        # Log version should have negative values
        assert np.any(spec_log < 0)
        # Linear version should be all non-negative
        assert np.all(spec_lin >= 0)

    def test_trim_silence(self):
        audio = np.zeros(44100)
        audio[10000:20000] = 0.5
        trimmed = trim_silence(audio, top_db=20)
        assert len(trimmed) < len(audio)
        assert len(trimmed) > 0


# ── MIDI utility tests ──────────────────────────────────────────────────

class TestMidiUtils:
    def test_save_and_load_midi(self, midi_file, sample_notes):
        assert midi_file.exists()
        loaded = load_midi(midi_file)
        assert len(loaded) == len(sample_notes)
        # First and last notes should match
        assert loaded[0][0] == pytest.approx(sample_notes[0][0], abs=0.01)
        assert loaded[-1][2] == sample_notes[-1][2]

    def test_midi_to_pretty_midi(self, sample_notes):
        pm = notes_to_pretty_midi(sample_notes, tempo=120)
        assert len(pm.instruments) == 1
        assert len(pm.instruments[0].notes) == 4

    def test_trim_sustained_noise(self, sample_notes):
        quiet_notes = sample_notes + [(1.0, 1.5, 50, 5)]  # very quiet
        trimmed = trim_sustained_noise(quiet_notes, max_vel_ratio=0.4)
        assert len(trimmed) == len(sample_notes)
        assert (50, 5) not in [(n[2], n[3]) for n in trimmed]

    def test_export_musicxml(self, tmp_path, sample_notes):
        path = tmp_path / "test.xml"
        result = export_musicxml(sample_notes, path)
        assert result.exists()
        assert result.suffix == ".xml"


# ── Quantizer tests ─────────────────────────────────────────────────────

class TestBeatMap:
    def test_beat_map_creation(self):
        beats = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
        downbeats = np.array([0.0, 2.0])
        bm = BeatMap(
            beats=beats,
            downbeats=downbeats,
            tempo=120.0,
            swing_ratio=0.0,
            time_signature="4/4",
        )
        assert len(bm.beats) == 5
        assert bm.tempo == 120.0
        assert bm.swing_ratio == 0.0


class TestQuantizer:
    def test_grid_building_straight(self):
        beats = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
        bm = BeatMap(beats, np.array([0.0, 2.0]), 120.0, 0.0, "4/4")
        quantizer = RhythmicQuantizer(QuantizerConfig(grid_resolution="8th"))
        grid = quantizer._build_grid(bm)
        # 5 beats × 2 subdivisions = 9 grid points (beats, includes last)
        assert len(grid) == 9

    def test_grid_building_16th(self):
        beats = np.array([0.0, 0.5, 1.0])
        bm = BeatMap(beats, np.array([0.0]), 120.0, 0.0, "4/4")
        quantizer = RhythmicQuantizer(QuantizerConfig(grid_resolution="16th"))
        grid = quantizer._build_grid(bm)
        # 2 beat intervals × 4 subdivisions = 9 points
        assert len(grid) == 9

    def test_grid_building_with_swing(self):
        beats = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
        bm = BeatMap(beats, np.array([0.0, 2.0]), 120.0, 0.67, "4/4")
        quantizer = RhythmicQuantizer(QuantizerConfig(grid_resolution="8th"))
        grid = quantizer._build_grid(bm)
        assert len(grid) == 9

    def test_snap_to_grid(self):
        beats = np.array([0.0, 0.5, 1.0])
        bm = BeatMap(beats, np.array([0.0]), 120.0, 0.0, "4/4")
        quantizer = RhythmicQuantizer()
        grid = quantizer._build_grid(bm)

        snapped = quantizer._snap_to_grid(0.26, grid, bm)
        assert snapped == pytest.approx(0.25, abs=0.02)

    def test_deduplicate(self):
        notes = [
            (0.0, 0.5, 60, 100),
            (0.0, 0.5, 60, 80),   # duplicate, quieter
            (0.0, 0.75, 60, 90),  # overlapping, same pitch
            (0.5, 1.0, 67, 100),
        ]
        quantizer = RhythmicQuantizer()
        deduped = quantizer._deduplicate(notes)
        # Should merge to 2 notes (first merged with second and third)
        assert len(deduped) <= 3

    def test_quantize_notes_simple(self):
        beats = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
        bm = BeatMap(beats, np.array([0.0, 2.0]), 120.0, 0.0, "4/4")
        quantizer = RhythmicQuantizer(QuantizerConfig(grid_resolution="8th"))

        notes = [
            (0.01, 0.24, 60, 100),    # should snap to 0.0, 0.25
            (0.26, 0.49, 64, 100),    # should snap to 0.25, 0.5
        ]
        quantized = quantizer._quantize_notes(notes, bm)
        assert len(quantized) == 2
        assert quantized[0][0] == pytest.approx(0.0, abs=0.05)


# ── Evaluator tests ─────────────────────────────────────────────────────

class TestEvaluator:
    def test_evaluate_perfect(self):
        from jazz_solo.training.evaluate import TranscriptionEvaluator
        ev = TranscriptionEvaluator(onset_tolerance=0.05)
        notes = [(0.0, 0.5, 60, 100), (0.5, 1.0, 64, 100)]
        metrics = ev.evaluate(notes, notes)  # same = perfect
        assert metrics["onset_f1"] == pytest.approx(1.0, abs=0.01)
        assert metrics["note_f1"] >= 0.8  # close to 1.0

    def test_evaluate_empty(self):
        from jazz_solo.training.evaluate import TranscriptionEvaluator
        ev = TranscriptionEvaluator()
        metrics = ev.evaluate([], [(0.0, 0.5, 60, 100)])
        assert metrics["onset_f1"] == 0.0
        assert metrics["estimated_count"] == 0

    def test_evaluate_worst(self):
        from jazz_solo.training.evaluate import TranscriptionEvaluator
        ev = TranscriptionEvaluator()
        ref = [(0.0, 0.5, 60, 100)]
        est = [(10.0, 10.5, 72, 100)]  # way off
        metrics = ev.evaluate(est, ref)
        assert metrics["onset_f1"] < 0.1
        assert metrics["estimated_count"] == 1


# ── Pipeline integration tests ──────────────────────────────────────────

class TestPipeline:
    def test_pipeline_initialization(self):
        from jazz_solo.pipeline.orchestrator import JazzSoloPipeline
        pipeline = JazzSoloPipeline()
        assert pipeline.separator is not None
        assert pipeline.transcriber is not None
        assert pipeline.quantizer is not None

    def test_pipeline_config_override(self):
        config = PipelineConfig(
            separator=SeparatorConfig(stem="vocals"),
        )
        from jazz_solo.pipeline.orchestrator import JazzSoloPipeline
        pipeline = JazzSoloPipeline(config)
        assert pipeline.config.separator.stem == "vocals"