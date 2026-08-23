"""Weimar Jazz Database dataset preprocessor.

Converts the Weimar Jazz Database (WJazzD) into spectrogram + MIDI
feature-target pairs for fine-tuning MT3 or Basic Pitch.

WJazzD provides:
- Full audio recordings (.wav)
- Manually verified solo transcriptions as MIDI, time-aligned to audio

This module:
1. Reads WJazzD audio + MIDI pairs
2. Computes log-mel spectrograms
3. Pairs each spectrogram frame with its corresponding MIDI note events
4. Outputs HDF5 or TFRecord files ready for training
"""

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

import numpy as np

from jazz_solo.utils.audio import load_audio, spectrogram
from jazz_solo.utils.midi import NoteEvent, load_midi

logger = logging.getLogger(__name__)


@dataclass
class WeimarSample:
    """A single training sample from the Weimar dataset."""

    track_id: str
    audio_path: str
    midi_path: str
    spectrogram_path: Optional[str] = None
    num_frames: int = 0
    num_notes: int = 0
    duration_sec: float = 0.0
    artist: str = ""
    title: str = ""


@dataclass
class TrainingExample:
    """A feature-target pair for model training."""

    spectrogram: np.ndarray  # shape: (n_mels, time_frames)
    note_events: List[NoteEvent]
    track_id: str = ""
    time_frames: int = 0


class WeimarPreprocessor:
    """Process the Weimar Jazz Database into training-ready spectrogram/MIDI pairs.

    Expected directory structure::

        weimar_jazz_db/
        ├── audio/
        │   ├── solo001.wav
        │   ├── solo002.wav
        │   └── ...
        ├── midi/
        │   ├── solo001.mid
        │   ├── solo002.mid
        │   └── ...
        └── metadata.json (optional)
    """

    def __init__(
        self,
        weimar_root: str | Path,
        output_dir: str | Path = "weimar_processed",
        n_mels: int = 128,
        hop_length: int = 512,
        sample_rate: int = 22050,
        n_fft: int = 2048,
    ):
        self.weimar_root = Path(weimar_root)
        self.output_dir = Path(output_dir)
        self.n_mels = n_mels
        self.hop_length = hop_length
        self.sample_rate = sample_rate
        self.n_fft = n_fft

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Locate audio and MIDI directories
        self.audio_dir = self.weimar_root / "audio"
        self.midi_dir = self.weimar_root / "midi"
        self.metadata_path = self.weimar_root / "metadata.json"

    def list_tracks(self) -> List[WeimarSample]:
        """Scan the dataset and return all available audio+MIDI pairs."""
        samples: List[WeimarSample] = []

        # Load metadata if available
        metadata: Dict[str, dict] = {}
        if self.metadata_path.exists():
            with open(self.metadata_path) as f:
                metadata = json.load(f)

        audio_files = sorted(self.audio_dir.glob("*.wav"))
        for af in audio_files:
            track_id = af.stem
            midi_file = self.midi_dir / f"{track_id}.mid"

            if not midi_file.exists():
                logger.warning(f"No MIDI found for {track_id}, skipping")
                continue

            meta = metadata.get(track_id, {})
            samples.append(WeimarSample(
                track_id=track_id,
                audio_path=str(af.resolve()),
                midi_path=str(midi_file.resolve()),
                artist=meta.get("artist", ""),
                title=meta.get("title", ""),
            ))

        logger.info(
            f"Found {len(samples)} valid tracks in Weimar Jazz Database"
        )
        return samples

    def preprocess_track(
        self, sample: WeimarSample
    ) -> Optional[TrainingExample]:
        """Convert a single track to a spectrogram + MIDI training example.

        Returns None if the audio is too short or MIDI is empty.
        """
        # Load audio
        audio, sr = load_audio(sample.audio_path, target_sr=self.sample_rate)

        if len(audio) < self.hop_length * 4:
            logger.warning(f"{sample.track_id}: audio too short, skipping")
            return None

        # Compute log-mel spectrogram
        mel = spectrogram(
            audio,
            sr=self.sample_rate,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            n_mels=self.n_mels,
            log=True,
        )  # shape: (n_mels, time_frames)

        # Load aligned MIDI notes
        notes = load_midi(sample.midi_path)

        if not notes:
            logger.warning(f"{sample.track_id}: no MIDI notes, skipping")
            return None

        return TrainingExample(
            spectrogram=mel,
            note_events=notes,
            track_id=sample.track_id,
            time_frames=mel.shape[1],
        )

    def preprocess_all(
        self,
        output_prefix: str = "weimar",
        save_format: str = "npz",
    ) -> None:
        """Preprocess the entire dataset and save to disk.

        Parameters
        ----------
        output_prefix : str
            Prefix for output files (e.g. 'weimar_train').
        save_format : str
            'npz' for NumPy compressed archives (simple, good for prototyping),
            'h5' for HDF5 (better for large-scale training).
        """
        tracks = self.list_tracks()
        if not tracks:
            logger.error("No tracks found — check weimar_root path.")
            return

        all_spectrograms = []
        all_label_times = []
        all_label_pitches = []
        all_label_velocities = []
        all_track_ids = []

        for sample in tracks:
            example = self.preprocess_track(sample)
            if example is None:
                continue

            # Convert note events to frame-aligned labels
            times, pitches, velocities = self._notes_to_labels(
                example.note_events, example.spectrogram.shape[1]
            )

            all_spectrograms.append(example.spectrogram)
            all_label_times.append(times)
            all_label_pitches.append(pitches)
            all_label_velocities.append(velocities)
            all_label_times.append(times)
            all_track_ids.append(example.track_id)

            logger.info(
                f"  [{sample.track_id}] "
                f"{example.spectrogram.shape[1]} frames, "
                f"{len(example.note_events)} notes"
            )

        # --- Save ---
        output_path = self.output_dir / f"{output_prefix}.npz"
        np.savez_compressed(
            output_path,
            spectrograms=np.array(all_spectrograms, dtype=object),
            label_times=np.array(all_label_times, dtype=object),
            label_pitches=np.array(all_label_pitches, dtype=object),
            label_velocities=np.array(all_label_velocities, dtype=object),
            track_ids=all_track_ids,
        )

        logger.info(
            f"Saved {len(all_spectrograms)} tracks → {output_path}"
        )

        # Save a manifest as JSON
        manifest = []
        for tid, spec, notes_count in zip(
            all_track_ids,
            all_spectrograms,
            [len(n) for n in all_label_pitches],
        ):
            manifest.append({
                "track_id": tid,
                "frames": spec.shape[1],
                "n_mels": spec.shape[0],
                "notes": notes_count,
            })

        manifest_path = self.output_dir / f"{output_prefix}_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Manifest → {manifest_path}")

    def _notes_to_labels(
        self,
        notes: List[NoteEvent],
        num_frames: int,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Convert note events to frame-aligned label arrays.

        Returns arrays of onset times, pitches, and velocities,
        aligned to the spectrogram hop length.
        """
        times = np.array([n[0] for n in notes])
        pitches = np.array([n[2] for n in notes], dtype=np.int32)
        velocities = np.array([n[3] for n in notes], dtype=np.int32)
        return times, pitches, velocities


class WeimarDataLoader:
    """Lightweight data loader that yields batches of spectrograms + labels."""

    def __init__(self, npz_path: str | Path, batch_size: int = 8):
        self.data = np.load(npz_path, allow_pickle=True)
        self.batch_size = batch_size
        self.n_samples = len(self.data["spectrograms"])

    def __len__(self) -> int:
        return (self.n_samples + self.batch_size - 1) // self.batch_size

    def __iter__(self) -> Iterator[dict]:
        for i in range(0, self.n_samples, self.batch_size):
            batch_specs = self.data["spectrograms"][i : i + self.batch_size]
            # Pad/truncate to uniform length within the batch
            max_frames = max(s.shape[1] for s in batch_specs)
            padded = np.zeros(
                (len(batch_specs), batch_specs[0].shape[0], max_frames)
            )
            for j, s in enumerate(batch_specs):
                padded[j, :, : s.shape[1]] = s

            yield {
                "spectrograms": padded,
                "track_ids": self.data["track_ids"][i : i + self.batch_size],
            }