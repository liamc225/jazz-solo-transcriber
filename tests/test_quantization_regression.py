import numpy as np
import pytest
from jazz_solo.config import QuantizerConfig
from jazz_solo.pipeline.quantizer import BeatMap, RhythmicQuantizer


def test_default_does_not_apply_unreliable_auto_swing(monkeypatch):
    q = RhythmicQuantizer(QuantizerConfig(grid_resolution='16th'))
    b = BeatMap(np.array([0., .5, 1.]), np.array([0.]), 120., .7, '4/4')
    monkeypatch.setattr(q, '_build_beat_map', lambda _: b)
    assert q.align([(.125, .25, 60, 100)], 'unused')[0][0] == pytest.approx(.125)


def test_swing_warps_eighth_midpoint_without_reordering_grid():
    q = RhythmicQuantizer(QuantizerConfig(grid_resolution='16th'))
    b = BeatMap(np.array([0., .5, 1.]), np.array([0.]), 120., 2/3, '4/4')
    assert q._build_grid(b)[:5] == pytest.approx([0, 1/6, 1/3, 5/12, .5])
