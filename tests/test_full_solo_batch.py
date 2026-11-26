import json
from pathlib import Path
import pytest
from jazz_solo.full_solo_batch import validate_manifest, run_batch


def test_manifest_rejects_invalid_boundaries_and_duplicate_ids(tmp_path):
    src = tmp_path / 'track.wav'
    src.touch()
    row = {'id':'solo-1','source':str(src),'start':1.,'end':3.}
    assert validate_manifest([row])[0]['id'] == 'solo-1'
    with pytest.raises(ValueError): validate_manifest([row, row])
    with pytest.raises(ValueError): validate_manifest([{**row, 'end':.5}])
    with pytest.raises(ValueError): validate_manifest([{**row, 'id':'../bad'}])


def test_batch_records_success_and_continues_after_failure(tmp_path, monkeypatch):
    source = tmp_path / 'track.wav'; source.touch()
    entries = validate_manifest([{'id':'one','source':str(source),'start':0,'end':2},
                                 {'id':'two','source':str(source),'start':2,'end':4}])
    def fake_clip(src, target, start, end):
        if start == 2: raise RuntimeError('test failure')
        target.touch()
    class FakePipeline:
        def transcribe(self, audio, output_dir, skip_separation=False):
            output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / '01_raw_transcription.mid').touch()
            (output_dir / '05_swing_reading.musicxml').touch()
            return [(0, 1, 60, 90)]
    monkeypatch.setattr('jazz_solo.full_solo_batch.clip_audio', fake_clip)
    result = run_batch(entries, tmp_path / 'output', pipeline=FakePipeline())
    assert [r['status'] for r in result] == ['complete', 'failed']
    assert json.loads((tmp_path / 'output' / 'results.json').read_text()) == result


def test_different_input_does_not_replace_completed_manifest(tmp_path, monkeypatch):
    src = tmp_path / 'track.wav'; src.touch()
    def fake_clip(src, target, start, end): target.touch()
    class FakePipeline:
        def transcribe(self, audio, output_dir, skip_separation=False):
            output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / '01_raw_transcription.mid').touch()
            (output_dir / '05_swing_reading.musicxml').touch()
            return [(0, 1, 60, 90)]
    monkeypatch.setattr('jazz_solo.full_solo_batch.clip_audio', fake_clip)
    original = validate_manifest([{'id':'one','source':str(src),'start':0,'end':2}])
    changed = validate_manifest([{'id':'one','source':str(src),'start':0,'end':3}])
    out = tmp_path / 'out'
    good = run_batch(original, out, pipeline=FakePipeline())[0]
    assert run_batch(changed, out, pipeline=FakePipeline())[0]['status'] == 'failed'
    assert json.loads((out/'results.json').read_text())[0] == good


def test_resume_detects_changed_source_file(tmp_path, monkeypatch):
    src = tmp_path / 'track.wav'; src.write_bytes(b'old')
    calls = []
    def fake_clip(src, target, start, end): calls.append(1); target.touch()
    class FakePipeline:
        def transcribe(self, audio, output_dir, skip_separation=False):
            out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
            (out/'01_raw_transcription.mid').touch(); (out/'05_swing_reading.musicxml').touch()
            return [(0,1,60,90)]
    monkeypatch.setattr('jazz_solo.full_solo_batch.clip_audio', fake_clip)
    entries = validate_manifest([{'id':'solo','source':str(src),'start':0,'end':2}])
    out = tmp_path/'out'
    assert run_batch(entries,out,pipeline=FakePipeline())[0]['status'] == 'complete'
    assert run_batch(entries,out,pipeline=FakePipeline())[0]['status'] == 'complete'
    assert len(calls) == 1
    src.write_bytes(b'new source audio')
    assert run_batch(entries,out,pipeline=FakePipeline())[0]['status'] == 'failed'
    assert len(calls) == 1
