import sqlite3
import pytest
from jazz_solo.training.benchmark_weimar import reference_excerpt


def test_reference_excerpt_uses_alignment_and_excludes_boundaries(tmp_path):
    db = tmp_path / 'test.db'
    with sqlite3.connect(db) as c:
        c.execute('create table melody (melid integer, onset real, pitch integer, duration real)')
        c.executemany('insert into melody values (?,?,?,?)', [
            (1, .1, 60, .2), (1, 1.0, 62, .3), (1, 3.0, 64, .2)])
    assert reference_excerpt(db, 1, 10, 10, 3, .25) == [(1.0, 1.3, 62, 100)]
    with pytest.raises(ValueError):
        reference_excerpt(db, 99, 10, 10, 3)


def test_reading_events_merge_ties_and_ignore_chord_symbols():
    from jazz_solo.training.benchmark_weimar import reading_events
    from jazz_solo.lead_sheet import build_lead_sheet
    score = build_lead_sheet([(1.5, 2.5, 60, 100)], 120, chords=[(0, 'F7')])
    events = reading_events(score, tempo=120, origin=0)
    assert len(events) == 1
    assert events[0][:3] == pytest.approx((1.5, 2.5, 60))


def test_swing_reading_events_convert_eighths_to_performed_time():
    from jazz_solo.training.benchmark_weimar import reading_events
    from jazz_solo.lead_sheet import build_lead_sheet
    score = build_lead_sheet([(0, .22, 60, 100), (.30, .46, 62, 100)],
                             tempo=120, rhythm='jazz', swing_ratio=.6)
    events = reading_events(score, tempo=120, origin=0, swing_ratio=.6)
    assert events[1][0] == pytest.approx(.30)
