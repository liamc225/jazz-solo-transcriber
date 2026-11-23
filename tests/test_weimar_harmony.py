import sqlite3
import pytest
from jazz_solo.training.weimar_harmony import extract_chords, convert_chord


def test_weimar_chord_conventions_are_explicit():
    assert convert_chord('C-7') == 'Cm7'
    assert convert_chord('Bbj7') == 'B-maj7'
    assert convert_chord('Em7b5') == 'Em7b5'
    assert convert_chord('NC') == 'N.C.'
    with pytest.raises(ValueError):
        convert_chord('not-a-chord')


def test_extracts_prior_chord_and_timed_changes(tmp_path):
    db = tmp_path / 'w.db'
    with sqlite3.connect(db) as c:
        c.execute('create table beats (melid integer, onset real, chord text)')
        c.executemany('insert into beats values (?,?,?)', [(4,1,'C-7'),(4,2,''),(4,3,'F7'),(4,7,'Bb')])
    result=extract_chords(db, 4, 10, 12, -0.5, 4)
    assert result == [{'time': -.5, 'symbol': 'Cm7'}, {'time': 1., 'symbol': 'F7'}]
