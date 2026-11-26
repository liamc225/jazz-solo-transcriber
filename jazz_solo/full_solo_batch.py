"""Run a resumable batch of explicitly bounded local solo recordings.

Input is a JSON list of {id, source, start, end, optional skip_separation};
start/end are seconds in the source audio. The caller must verify the take and
solo boundaries. Results are machine drafts and are not accuracy-verified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path


def validate_manifest(entries):
    """Validate solo IDs, source files and explicit full-solo boundaries."""
    if not isinstance(entries, list):
        raise ValueError('manifest must be a list')
    seen = set()
    result = []
    for row in entries:
        ident = row.get('id')
        if not isinstance(ident, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,95}', ident):
            raise ValueError('solo ID must contain only letters, numbers, underscore or hyphen')
        if ident in seen:
            raise ValueError(f'duplicate solo ID: {ident}')
        seen.add(ident)
        source = Path(row['source']).expanduser().resolve()
        if not source.is_file():
            raise ValueError(f'source is not a file: {source}')
        start, end = float(row['start']), float(row['end'])
        if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end <= start:
            raise ValueError(f'invalid solo boundaries: {ident}')
        skip = row.get('skip_separation', False)
        if not isinstance(skip, bool):
            raise ValueError('skip_separation must be boolean')
        result.append({**row, 'source': str(source), 'start': start, 'end': end,
                       'skip_separation': skip})
    return result


def clip_audio(source, target, start, end):
    """Create a local WAV excerpt without modifying the source."""
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(start), '-t', str(end - start),
                    '-i', str(source), '-ar', '44100', str(target)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def run_batch(entries, output_dir, pipeline=None):
    """Process entries serially, record failures, and resume identical completed jobs."""
    if pipeline is None:
        from jazz_solo.pipeline.orchestrator import JazzSoloPipeline
        pipeline = JazzSoloPipeline()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = output_dir / 'results.json'
    previous = {r['id']: r for r in json.loads(report.read_text())} if report.exists() else {}
    results = []
    for item in entries:
        ident = item['id']
        key = {k: item[k] for k in ('id', 'source', 'start', 'end', 'skip_separation')}
        source_stat = Path(item['source']).stat()
        key.update({'source_size': source_stat.st_size, 'source_mtime_ns': source_stat.st_mtime_ns})
        fingerprint = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()
        folder = output_dir / ident
        prior = previous.get(ident)
        conflict = bool((prior and prior.get('fingerprint') != fingerprint) or
                        (not prior and folder.exists()))
        if conflict:
            result = {'id': ident, 'status': 'failed', 'fingerprint': fingerprint,
                      'error': 'output exists for different inputs; choose a new ID'}
        elif (prior and prior.get('status') == 'complete' and
              (folder / '01_raw_transcription.mid').is_file() and
              (folder / '05_swing_reading.musicxml').is_file()):
            result = prior
        else:
            try:
                folder.mkdir(parents=True, exist_ok=True)
                wav = folder / 'solo.wav'
                clip_audio(item['source'], wav, item['start'], item['end'])
                notes = pipeline.transcribe(wav, output_dir=folder,
                                            skip_separation=item['skip_separation'])
                if (not notes or not (folder / '01_raw_transcription.mid').is_file() or
                        not (folder / '05_swing_reading.musicxml').is_file()):
                    raise RuntimeError('required MIDI or swing reading copy was not generated')
                result = {'id': ident, 'status': 'complete', 'fingerprint': fingerprint,
                          'note_count': len(notes), 'output': str(folder)}
            except Exception as exc:
                result = {'id': ident, 'status': 'failed', 'fingerprint': fingerprint,
                          'error': f'{type(exc).__name__}: {exc}'}
        results.append(result)
        # Keep earlier records when the user resumes a subset of the manifest.
        if not conflict:
            previous[ident] = result
        tmp = report.with_suffix('.tmp')
        tmp.write_text(json.dumps(list(previous.values()), indent=2) + '\n')
        tmp.replace(report)
        print(f"{ident}: {result['status']}", flush=True)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    entries = validate_manifest(json.loads(args.manifest.read_text()))
    results = run_batch(entries, args.output_dir)
    raise SystemExit(1 if any(r['status'] != 'complete' for r in results) else 0)


if __name__ == '__main__':
    main()
