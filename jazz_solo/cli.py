"""Command-line interface for the jazz solo transcriber."""

import logging
import sys
from pathlib import Path

import click

from jazz_solo.config import (
    PipelineConfig,
    SeparatorConfig,
    TranscriberConfig,
    QuantizerConfig,
)
from jazz_solo.pipeline.orchestrator import JazzSoloPipeline

logger = logging.getLogger(__name__)


@click.group()
@click.option("-v", "--verbose", count=True, help="Increase verbosity")
@click.option(
    "--log-file", type=click.Path(path_type=Path), help="Log to file"
)
def cli(verbose: int, log_file: Path | None) -> None:
    """🎷 Jazz Solo Transcriber — AI-powered jazz transcription pipeline.

    Transforms raw jazz recordings into quantised MIDI and MusicXML scores.
    """
    level = logging.WARNING
    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=log_file.open("w") if log_file else sys.stderr,
    )


@cli.command()
@click.argument("input", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o", "--output-dir", type=click.Path(path_type=Path),
    help="Output directory (default: <input_stem>_transcription/)",
)
@click.option("--model", default="htdemucs", help="Demucs model variant")
@click.option("--device", default="cpu", help="Compute device (cpu/cuda)")
@click.option("--skip-separation", is_flag=True, help="Input is already a solo track")
@click.option("--stem", default="other", help="Stem to extract (vocals/other/drums/bass)")
@click.option("--transcriber", default="basic-pitch", help="Transcriber backend (basic-pitch/mt3)")
@click.option("--onset-threshold", default=0.5, type=float, help="Onset detection threshold")
@click.option("--frame-threshold", default=0.3, type=float, help="Frame activation threshold")
@click.option("--min-note-length", default=0.058, type=float, help="Minimum note length (sec)")
@click.option("--grid", default="16th", help="Quantization grid resolution")
@click.option("--swing", default=0.0, type=float, help="Swing ratio (0=auto)")
@click.option("--bpm", default=(40.0, 400.0), nargs=2, type=float,
              help="Min and max BPM for beat tracking")
def transcribe(
    input: Path,
    output_dir: Path | None,
    model: str,
    device: str,
    skip_separation: bool,
    stem: str,
    transcriber: str,
    onset_threshold: float,
    frame_threshold: float,
    min_note_length: float,
    grid: str,
    swing: float,
    bpm: tuple[float, float],
) -> None:
    """Transcribe a jazz recording into MIDI and MusicXML."""
    config = PipelineConfig(
        separator=SeparatorConfig(
            model=model, device=device, stem=stem,
        ),
        transcriber=TranscriberConfig(
            model=transcriber,
            onset_threshold=onset_threshold,
            frame_threshold=frame_threshold,
            minimum_note_length=min_note_length,
            device=device,
        ),
        quantizer=QuantizerConfig(
            grid_resolution=grid,
            swing_ratio=swing,
            min_bpm=bpm[0],
            max_bpm=bpm[1],
        ),
        skip_separation=skip_separation,
    )

    pipeline = JazzSoloPipeline(config)
    notes = pipeline.transcribe(input, output_dir=output_dir)

    if not notes:
        click.echo("⚠️  No notes detected. Try adjusting onset/frame thresholds.", err=True)
        sys.exit(1)

    click.echo(f"✅ {len(notes)} notes transcribed → {output_dir or input.stem + '_transcription'}")


@cli.command()
@click.argument("midi_file", type=click.Path(exists=True, path_type=Path))
def info(midi_file: Path) -> None:
    """Display information about a transcribed MIDI file."""
    from jazz_solo.utils.midi import load_midi

    notes = load_midi(midi_file)
    if not notes:
        click.echo("No notes found in MIDI file.")
        return

    pitches = sorted(set(n[2] for n in notes))
    dur = notes[-1][1] - notes[0][0]
    click.echo(f"  Notes:      {len(notes)}")
    click.echo(f"  Duration:   {dur:.1f}s")
    click.echo(f"  Pitch range: {pitches[0]}–{pitches[-1]} ({pitches[-1] - pitches[0]} semitones)")
    click.echo(f"  Density:    {len(notes) / max(dur, 0.1):.1f} notes/sec")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()