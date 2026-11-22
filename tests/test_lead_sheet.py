import pytest
from jazz_solo.lead_sheet import build_lead_sheet


def test_seconds_become_beats_and_overlaps_are_resolved():
    notes = [(0.0, 0.5, 60, 100), (0.0, 0.5, 48, 40), (0.5, 1.0, 62, 100)]
    part = build_lead_sheet(notes, tempo=120, beat_origin=0).parts[0]
    found = [(float(n.getOffsetInHierarchy(part)), float(n.quarterLength), n.pitch.midi)
             for n in part.recurse().notes]
    assert found == [(0, 1, 60), (1, 1, 62)]


def test_nonpositive_tempo_rejected():
    with pytest.raises(ValueError):
        build_lead_sheet([], tempo=0)


def test_silences_are_visible_rests():
    import music21
    score = build_lead_sheet([(0.5, 1.0, 60, 100)], tempo=120)
    rests = list(score.recurse().getElementsByClass(music21.note.Rest))
    assert rests
    assert float(rests[0].quarterLength) == 1.0
    assert not rests[0].style.hideObjectOnPrint


def test_explicit_downbeat_preserves_bar_position():
    score = build_lead_sheet([(0.0, .5, 60, 100)], tempo=120, downbeat_origin=-.5)
    part = score.parts[0]
    note = list(part.recurse().notes)[0]
    assert float(note.getOffsetInHierarchy(part)) == pytest.approx(1.0)


def test_thirty_second_note_grid_preserves_short_notes():
    score = build_lead_sheet([(0, .125, 60, 100)], tempo=60, subdivisions=8)
    note = list(score.parts[0].recurse().notes)[0]
    assert float(note.quarterLength) == pytest.approx(.125)
