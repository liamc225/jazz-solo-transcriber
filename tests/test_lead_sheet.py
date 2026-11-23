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


def test_explicit_key_and_chord_symbols_survive_musicxml(tmp_path):
    import music21
    score = build_lead_sheet(
        [(0, .5, 70, 100), (.5, 1, 72, 100)], 120,
        key_signature='B-', chords=[(0.0, 'Cm7'), (.5, 'F7')],
    )
    path = tmp_path / 'score.musicxml'
    score.write('musicxml', fp=str(path))
    parsed = music21.converter.parse(path)
    assert parsed.recurse().getElementsByClass(music21.key.KeySignature)[0].sharps == -2
    symbols = list(parsed.recurse().getElementsByClass(music21.harmony.ChordSymbol))
    assert [s.figure for s in symbols] == ['Cm7', 'F7']


def test_harmony_is_not_guessed():
    import music21
    score = build_lead_sheet([(0, .5, 60, 100)], 120)
    assert not list(score.recurse().getElementsByClass(music21.harmony.ChordSymbol))


def test_optional_pitch_range_filters_only_when_requested():
    notes = [(0, .5, 42, 100), (.5, 1, 60, 100), (1, 1.5, 87, 100)]
    part = build_lead_sheet(notes, 120, pitch_range=(48, 84)).parts[0]
    assert [n.pitch.midi for n in part.recurse().notes] == [60]
    assert len(list(build_lead_sheet(notes, 120).parts[0].recurse().notes)) == 3
    with pytest.raises(ValueError):
        build_lead_sheet(notes, 120, pitch_range=(84, 48))


def test_flat_chord_root_is_not_mistaken_for_natural():
    import music21
    score = build_lead_sheet([(0, .5, 70, 100)], 120, chords=[(0, 'Bb7')])
    chord = list(score.recurse().getElementsByClass(music21.harmony.ChordSymbol))[0]
    assert chord.root().pitchClass == 10


def test_chords_landing_on_same_beat_do_not_overlap():
    import music21
    score = build_lead_sheet([(0, .5, 65, 100)], 120,
                             chords=[(-.01, 'F7'), (.01, 'C7')])
    chords = list(score.recurse().getElementsByClass(music21.harmony.ChordSymbol))
    assert len(chords) == 1
    assert chords[0].figure == 'C7'


def test_jazz_notation_writes_swung_eighths_as_even_eighths():
    score = build_lead_sheet([(0, .22, 60, 100), (.30, .46, 62, 100)],
                             tempo=120, rhythm='jazz', swing_ratio=.6)
    part = score.parts[0]
    notes = list(part.recurse().getElementsByClass('Note'))
    assert [float(n.getOffsetInHierarchy(part)) for n in notes] == pytest.approx([0, .5])
    assert [float(n.quarterLength) for n in notes] == pytest.approx([.5, .5])


def test_jazz_notation_keeps_fast_sixteenth_notes():
    score = build_lead_sheet([(0, .09, 60, 100), (.15, .23, 62, 100)],
                             tempo=120, rhythm='jazz', swing_ratio=.6)
    notes = list(score.parts[0].recurse().getElementsByClass('Note'))
    assert len(notes) == 2
    assert float(notes[1].getOffsetInHierarchy(score.parts[0])) == pytest.approx(.25)


def test_specified_six_four_meter_controls_bars_and_export(tmp_path):
    import music21
    score = build_lead_sheet([(0, .5, 60, 100), (2.5, 3, 62, 100)],
                             tempo=120, time_signature='6/4')
    path = tmp_path / 'six_four.musicxml'
    score.write('musicxml', fp=str(path))
    result = music21.converter.parse(path)
    assert result.recurse().getElementsByClass(music21.meter.TimeSignature)[0].ratioString == '6/4'
    assert len(result.parts[0].getElementsByClass(music21.stream.Measure)) == 1


def test_guitar_reading_uses_octave_clef_and_preserves_sounding_pitch(tmp_path):
    import music21
    score = build_lead_sheet([(0, .5, 52, 100)], tempo=120, guitar_octave=True)
    path = tmp_path / 'guitar.musicxml'
    score.write('musicxml', fp=str(path))
    xml = path.read_text()
    assert '<clef-octave-change>-1</clef-octave-change>' in xml
    parsed = music21.converter.parse(path)
    notes = list(parsed.recurse().getElementsByClass(music21.note.Note))
    assert notes[0].pitch.midi == 52


def test_system_breaks_every_four_bars_preserves_notes(tmp_path):
    notes = [(float(i), float(i) + .5, 60 + i % 8, 90) for i in range(12)]
    score = build_lead_sheet(notes, tempo=60, bars_per_system=2)
    path = tmp_path / 'systems.musicxml'
    score.write('musicxml', fp=str(path))
    assert 'new-system="yes"' in path.read_text()
    import music21
    parsed = music21.converter.parse(path)
    assert len(list(parsed.recurse().getElementsByClass(music21.note.Note))) == 12


def test_optional_confidence_cutoff_does_not_modify_default():
    notes = [(0., .5, 60, 40), (.5, 1., 62, 80)]
    assert len(list(build_lead_sheet(notes, 120).parts[0].recurse().notes)) == 2
    part = build_lead_sheet(notes, 120, min_velocity=60).parts[0]
    assert [n.pitch.midi for n in part.recurse().notes] == [62]
    with pytest.raises(ValueError):
        build_lead_sheet(notes, 120, min_velocity=128)


def test_guitar_range_prevents_louder_bass_from_replacing_melody():
    notes = [(0.0, .15, 43, 65), (0.01, .15, 62, 53)]
    part = build_lead_sheet(notes, tempo=200, rhythm='jazz', pitch_range=(50, 84),
                            min_velocity=40).parts[0]
    assert [n.pitch.midi for n in part.recurse().getElementsByClass('Note')] == [62]
