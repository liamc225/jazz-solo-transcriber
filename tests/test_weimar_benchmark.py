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
