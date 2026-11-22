import pytest
from jazz_solo.training.evaluate import TranscriptionEvaluator


def test_pitch_matching_uses_midi_as_notes_not_hertz():
    reference = [(0.0, 0.4, 60, 100)]
    wrong = [(0.0, 0.4, 61, 100)]
    metrics = TranscriptionEvaluator().evaluate(wrong, reference)
    assert metrics['onset_f1'] == pytest.approx(1)
    assert metrics['note_f1'] == pytest.approx(0)
    assert metrics['pitch_accuracy'] == pytest.approx(0)


def test_pitch_accuracy_for_identical_notes():
    notes = [(0.0, 0.4, 60, 100), (0.5, 0.9, 64, 100)]
    metrics = TranscriptionEvaluator().evaluate(notes, notes)
    assert metrics['note_f1'] == pytest.approx(1)
    assert metrics['pitch_accuracy'] == pytest.approx(1)


def test_onset_precision_recall_and_f1_are_not_swapped():
    reference = [(0.0, .2, 60, 100), (.5, .7, 62, 100)]
    estimated = [(0.0, .2, 60, 100)]
    metrics = TranscriptionEvaluator().evaluate(estimated, reference)
    assert metrics['onset_precision'] == pytest.approx(1)
    assert metrics['onset_recall'] == pytest.approx(.5)
    assert metrics['onset_f1'] == pytest.approx(2/3)
