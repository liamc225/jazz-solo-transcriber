import json
import pytest
from jazz_solo.training.benchmark_guitarset import guitarset_reference, evaluate_guitarset


def test_read_multistring_jams_and_velocity_filter(tmp_path):
    path = tmp_path / 'fixture.jams'
    path.write_text(json.dumps({'annotations': [
        {'namespace':'note_midi','data':[{'time':0.,'duration':.3,'value':60.1}]},
        {'namespace':'note_midi','data':[{'time':.5,'duration':.3,'value':64.0}]},
        {'namespace':'beat_position','data':[]},
    ]}))
    reference = guitarset_reference(path)
    assert [x[2] for x in reference] == [60, 64]
    estimated = [(0., .3, 60, 100), (.5, .8, 64, 80), (1., 1.1, 70, 30)]
    unfiltered = evaluate_guitarset(estimated, reference)
    filtered = evaluate_guitarset(estimated, reference, min_velocity=60)
    assert unfiltered['note_precision'] == pytest.approx(2/3)
    assert filtered['note_f1'] == pytest.approx(1.)


def test_empty_note_annotations_rejected(tmp_path):
    path = tmp_path / 'empty.jams'
    path.write_text(json.dumps({'annotations': []}))
    with pytest.raises(ValueError):
        guitarset_reference(path)
