from types import SimpleNamespace
import music21
from jazz_solo.pipeline.orchestrator import JazzSoloPipeline


def test_pipeline_emits_tempo_correct_reading_copy(tmp_path, monkeypatch):
    pipeline = JazzSoloPipeline()
    notes = [(0.0, .5, 60, 100), (.5, 1., 62, 100)]
    monkeypatch.setattr(pipeline.transcriber, 'transcribe', lambda *a, **k: notes)
    def align(items, path):
        pipeline.quantizer.last_beat_map = SimpleNamespace(tempo=120., beats=[0., .5])
        return items
    monkeypatch.setattr(pipeline.quantizer, 'align', align)
    pipeline.transcribe(tmp_path / 'input.wav', output_dir=tmp_path / 'out', skip_separation=True)
    score = music21.converter.parse(tmp_path / 'out' / '04_reading_copy.musicxml')
    part = score.parts[0]
    found = list(part.recurse().getElementsByClass(music21.note.Note))
    assert [float(n.getOffsetInHierarchy(part)) for n in found] == [0., 1.]
    assert all(float(n.quarterLength) == 1 for n in found)


def test_pipeline_emits_swing_reading_copy(tmp_path, monkeypatch):
    pipeline = JazzSoloPipeline()
    notes = [(0., .22, 60, 100), (.3, .46, 62, 100)]
    monkeypatch.setattr(pipeline.transcriber, 'transcribe', lambda *a, **k: notes)
    def align(items, path):
        pipeline.quantizer.last_beat_map = SimpleNamespace(tempo=120., beats=[0., .5])
        return items
    monkeypatch.setattr(pipeline.quantizer, 'align', align)
    pipeline.transcribe(tmp_path / 'input.wav', output_dir=tmp_path / 'out', skip_separation=True)
    score = music21.converter.parse(tmp_path / 'out' / '05_swing_reading.musicxml')
    notes = list(score.parts[0].recurse().getElementsByClass(music21.note.Note))
    assert [float(n.getOffsetInHierarchy(score.parts[0])) for n in notes] == [0., .5]
