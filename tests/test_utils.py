"""Unit tests for pycrossfade.utils (run in the container stack)."""
import numpy as np
import pytest

from pycrossfade import utils
from pycrossfade import config


def _mono(n=4000, sr=44100):
    t = np.linspace(0.0, n / sr, n, endpoint=False)
    return (np.sin(2 * np.pi * 440 * t)).astype('float32')


def _stereo(n=4000, sr=44100):
    return np.stack([_mono(n, sr), 0.5 * _mono(n, sr)], axis=1).astype('float32')


# ---------- add_beep ----------
def test_add_beep_returns_copy_and_does_not_mutate_input():
    audio = _mono()
    original = audio.copy()
    out = utils.add_beep_to_audio(audio, beep_index=100)
    assert out is not audio
    assert np.array_equal(audio, original)  # input untouched
    assert out.shape == audio.shape


def test_add_beep_stereo_shape_preserved():
    audio = _stereo()
    out = utils.add_beep_to_audio(audio, beep_index=50, sample_rate=44100)
    assert out.shape == audio.shape


def test_add_beep_clips_at_end_without_error():
    audio = _mono(n=1000)
    out = utils.add_beep_to_audio(audio, beep_index=990)
    assert out.shape == audio.shape


# ---------- linear_fade_volume ----------
@pytest.mark.parametrize('profile', ['linear', 'cosine', 'equal_power'])
def test_linear_fade_volume_shape_preserved(profile):
    audio = _mono()
    out = utils.linear_fade_volume(audio, 0.0, 1.0, profile=profile)
    assert out.shape == audio.shape


def test_linear_fade_volume_stereo_aware():
    audio = _stereo()
    out = utils.linear_fade_volume(audio, 0.0, 1.0, profile='linear')
    assert out.shape == audio.shape


def test_linear_fade_volume_noop_when_equal():
    audio = _mono()
    out = utils.linear_fade_volume(audio, 0.5, 0.5)
    assert np.array_equal(out, audio)


# ---------- linear_fade_filter ----------
@pytest.mark.parametrize('filter_type', ['low_shelf', 'high_shelf'])
def test_linear_fade_filter_shape_preserved(filter_type):
    audio = _mono()
    out = utils.linear_fade_filter(audio, filter_type, 0.9, 0.0)
    assert out.shape == audio.shape
    assert np.isfinite(out).all()


def test_linear_fade_filter_stereo_aware():
    audio = _stereo()
    out = utils.linear_fade_filter(audio, 'low_shelf', 0.9, 0.0)
    assert out.shape == audio.shape


def test_linear_fade_filter_noop_when_equal():
    audio = _mono()
    out = utils.linear_fade_filter(audio, 'low_shelf', 0.5, 0.5)
    assert np.array_equal(out, audio)


def test_linear_fade_filter_unknown_type_raises():
    audio = _mono()
    with pytest.raises(ValueError):
        utils.linear_fade_filter(audio, 'bogus_shelf', 0.9, 0.0)


# ---------- crossfade_eq ----------
def test_crossfade_eq_lengths_match():
    master = _mono()
    slave = _mono()
    out = utils.crossfade_eq(master, slave, sample_rate=44100)
    assert out.shape == master.shape
    assert np.isfinite(out).all()


def test_crossfade_eq_stereo_aware():
    master = _stereo()
    slave = _stereo()
    out = utils.crossfade_eq(master, slave, sample_rate=44100)
    assert out.shape == master.shape


# ---------- click_protect ----------
def test_click_protect_length_preserved():
    audio = _mono()
    out = utils.click_protect(audio, [1000, 2000], sample_rate=44100)
    assert out.shape == audio.shape
    assert np.array_equal(out[:1000 - 133], audio[:1000 - 133])  # untouched core


# ---------- replay_gain_offset ----------
def test_replay_gain_offset_shape_preserved():
    audio = _mono()
    out = utils.replay_gain_offset(audio, -10.46)
    assert out.shape == audio.shape
    # negative gain should lower the signal
    assert np.mean(np.abs(out)) < np.mean(np.abs(audio))
