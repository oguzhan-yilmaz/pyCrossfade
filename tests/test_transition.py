"""Unit tests for pycrossfade.transition (run in the container stack)."""
import numpy as np
import pytest

from pycrossfade import transition
from pycrossfade import config
from pycrossfade.song import Song


SR = 44100


def make_song(n_bars=8, spb=22050):
    """Build a Song from synthetic audio + downbeats (no file IO)."""
    dbeats = np.arange(n_bars + 1) * spb
    audio = np.zeros(int(dbeats[-1] + spb), dtype=np.float32)
    song = Song()
    song.audio = audio
    song.downbeats = dbeats
    song.sample_rate = SR
    song.num_channels = 1
    return song


# ---------- time_stretch_gradually_in_downbeats ----------
def test_ts_factors_reach_endpoint():
    song = make_song(n_bars=6)
    audio = np.zeros(len(song.audio), dtype=np.float32)
    audio[::100] = 1.0  # give it some content so stretching is meaningful
    song.audio = audio
    out = transition.time_stretch_gradually_in_downbeats(song, 1.1)
    # output must be non-empty and finite
    assert out.size > 0
    assert np.isfinite(out).all()


def test_ts_factor_one_returns_audio_unchanged():
    song = make_song()
    audio = song.audio.copy()
    out = transition.time_stretch_gradually_in_downbeats(song, 1.0)
    assert np.array_equal(out, audio)


# ---------- beatmatch_to_slave ----------
def test_beatmatch_output_lengths_equal():
    master = make_song(n_bars=8)
    slave = make_song(n_bars=8, spb=18000)  # different BPM
    master.audio[::100] = 0.5
    slave.audio[::100] = 0.5
    out_master, out_slave = transition.beatmatch_to_slave(master, slave)
    assert len(out_master) == len(out_slave)


def test_beatmatch_requires_same_dbeat_count():
    master = make_song(n_bars=8)
    slave = make_song(n_bars=6)
    with pytest.raises(Exception):
        transition.beatmatch_to_slave(master, slave)


# ---------- crop_audio_and_dbeats ----------
def test_crop_basic_and_negative_bounds():
    song = make_song(n_bars=10)
    cropped = transition.crop_audio_and_dbeats(song, 2, 6)
    assert cropped.downbeats[0] == 0
    assert cropped.sample_rate == song.sample_rate

    # negative indexing: -2 -> 8, -1 -> 9
    cropped_neg = transition.crop_audio_and_dbeats(song, -2, -1)
    assert len(cropped_neg.downbeats) == 1


def test_crop_out_of_bounds_raises():
    song = make_song(n_bars=4)
    with pytest.raises(Exception):
        transition.crop_audio_and_dbeats(song, 0, 4)  # end >= len(dbeats)


# ---------- crossfade ----------
def test_crossfade_result_length_decomposition():
    master = make_song(n_bars=12, spb=20000)
    slave = make_song(n_bars=12, spb=20000)
    master.audio[::50] = 0.5
    slave.audio[::50] = 0.5

    result = transition.crossfade(master, slave, settings=config.CrossfadeSettings(
        len_crossfade=4, len_time_stretch=4))

    expected = (len(result.master_initial_audio)
                + len(result.time_stretch_audio)
                + len(result.crossfade_part_audio)
                + len(result.slave_remaining_audio))
    assert len(result.audio) == expected
    assert np.isfinite(result.audio).all()


def test_crossfade_legacy_dict_access_works():
    master = make_song(n_bars=12)
    slave = make_song(n_bars=12)
    master.audio[::50] = 0.5
    slave.audio[::50] = 0.5
    result = transition.crossfade(master, slave, settings=config.CrossfadeSettings())
    assert result['audio'] is result.audio  # dict-style access preserved
    assert result['len_crossfade'] == 8


def test_crossfade_returns_typed_transition():
    master = make_song(n_bars=12)
    slave = make_song(n_bars=12)
    master.audio[::50] = 0.5
    slave.audio[::50] = 0.5
    result = transition.crossfade(master, slave, settings=config.CrossfadeSettings())
    assert isinstance(result, transition.Transition)


# ---------- crossfade_multiple ----------
def test_crossfade_multiple_needs_three_songs():
    with pytest.raises(ValueError):
        transition.crossfade_multiple([make_song(), make_song()])


def test_crossfade_multiple_returns_typed_multi():
    songs = [make_song(n_bars=12), make_song(n_bars=12), make_song(n_bars=12)]
    for s in songs:
        s.audio[::50] = 0.5
    result = transition.crossfade_multiple(songs, settings=config.CrossfadeSettings())
    assert isinstance(result, transition.MultiTransition)
    assert result.full_transition.size > 0
    assert len(result.transition_indices) > 0
