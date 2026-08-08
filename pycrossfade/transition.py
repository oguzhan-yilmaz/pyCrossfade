import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional
from . import config
from .utils import time_stretch, linear_fade_volume, linear_fade_filter
from .song import Song


@dataclass
class Transition:
    """Typed result of a single two-song crossfade.

    ``audio`` is the full concatenated result. The component slices and their
    start indices/seconds are also exposed so callers can inspect or re-render
    the pieces. ``to_dict()`` (and dict-style ``['key']`` access) keep the
    legacy dict API working.
    """
    audio: np.ndarray = field(default=None)
    master_initial_audio: np.ndarray = field(default=None)
    time_stretch_audio: np.ndarray = field(default=None)
    crossfade_part_audio: np.ndarray = field(default=None)
    slave_remaining_audio: np.ndarray = field(default=None)
    slave_remaining_song: Optional[Song] = None
    time_stretch_start_idx: int = 0
    crossfade_start_idx: int = 0
    crossfade_end_idx: int = 0
    slave_start_idx: int = 0
    slave_fadein_end_idx: int = 0
    time_stretch_start_seconds: float = 0.0
    crossfade_start_seconds: float = 0.0
    crossfade_end_seconds: float = 0.0
    slave_start_seconds: float = 0.0
    slave_fadein_end_seconds: float = 0.0
    len_crossfade: int = 8
    len_time_stretch: int = 8

    def to_dict(self):
        return {
            'master_initial_audio': self.master_initial_audio,
            'slave_remaining_audio': self.slave_remaining_audio,
            'slave_remaining_song': self.slave_remaining_song,
            'audio': self.audio,
            'time_stretch_audio': self.time_stretch_audio,
            'crossfade_part_audio': self.crossfade_part_audio,
            'slave_fadein_end_idx': self.slave_fadein_end_idx,
            'time_stretch_start_idx': self.time_stretch_start_idx,
            'crossfade_start_idx': self.crossfade_start_idx,
            'crossfade_end_idx': self.crossfade_end_idx,
            'slave_start_idx': self.slave_start_idx,
            'time_stretch_start_seconds': self.time_stretch_start_seconds,
            'crossfade_start_seconds': self.crossfade_start_seconds,
            'crossfade_end_seconds': self.crossfade_end_seconds,
            'slave_start_seconds': self.slave_start_seconds,
            'slave_fadein_end_seconds': self.slave_fadein_end_seconds,
            'len_crossfade': self.len_crossfade,
            'len_time_stretch': self.len_time_stretch,
        }

    def __getitem__(self, key):
        """Legacy dict-style access (``crossfade['audio']``)."""
        return self.to_dict()[key]


@dataclass
class MultiTransition:
    """Typed result of a multi-song crossfade."""
    full_transition: np.ndarray = field(default=None)
    transition_indices: List[int] = field(default_factory=list)

    def to_dict(self):
        return {
            'full_transition': self.full_transition,
            'transition_indices': self.transition_indices,
        }

    def __getitem__(self, key):
        return self.to_dict()[key]



def time_stretch_gradually_in_downbeats(song, final_factor):
    """Time-stretch each downbeat fragment by a gradually increasing factor.

    Factors are built with ``np.linspace`` so the last fragment is guaranteed to
    reach ``final_factor`` (the old ``np.arange`` float-step could silently miss
    the endpoint). ``final_factor == 1`` is a clean early return.
    """
    audio = song.audio
    dbeats = song.get_downbeats()

    if final_factor == 1 or len(dbeats) < 2:
        return audio

    ts_factors = np.linspace(1.0, final_factor, len(dbeats))

    time_stretched_audio_slices = []
    for i in range(len(dbeats) - 1):
        factor = float(ts_factors[i])
        frag = audio[dbeats[i]:dbeats[i + 1]]
        time_stretched_audio_slices.append(time_stretch(frag, factor))

    output = np.concatenate(time_stretched_audio_slices)
    return output

def time_stretch_beatmatch_fragment(master_audio, master_cur_idx, master_next_idx,
                                   slave_cur_idx, slave_next_idx):
    """Time-stretch one master fragment so it lines up with a slave fragment.

    The stretch factor is the master/slave length ratio; the result is trimmed
    or zero-padded to exactly ``slave_next_idx - slave_cur_idx`` frames.
    """
    slave_dbeat_diff_idx = slave_next_idx - slave_cur_idx
    ts_factor = (master_next_idx - master_cur_idx) / slave_dbeat_diff_idx

    master_audio_frag = master_audio[master_cur_idx:master_next_idx]
    ts_maf = time_stretch(master_audio_frag, ts_factor)

    # floating-point stretch factors can overshoot/short the target length by a
    # few frames; trim or zero-pad so concatenation stays exact.
    if len(ts_maf) > slave_dbeat_diff_idx:
        return ts_maf[:slave_dbeat_diff_idx]
    if len(ts_maf) < slave_dbeat_diff_idx:
        pad = np.zeros(slave_dbeat_diff_idx - len(ts_maf))
        return np.concatenate((ts_maf, pad))
    return ts_maf


def beatmatch_to_slave(master_song, slave_song):
    master_audio = master_song.audio
    master_dbeats = master_song.get_downbeats()
    slave_audio = slave_song.audio
    slave_dbeats = slave_song.get_downbeats()

    if len(master_dbeats) != len(slave_dbeats):
        raise Exception(f"master_dbeats({len(master_dbeats)}) and slave_dbeats({len(slave_dbeats)}) is not same length")

    len_beatmatch_dbeats = len(master_dbeats)

    # Time stretching between every dbeat, according their respective time difference
    time_stretched_master_fadeout_audio_fragments = []
    for i in range(len_beatmatch_dbeats - 1):
        m_cur, m_next = master_dbeats[i], master_dbeats[i + 1]
        s_cur, s_next = slave_dbeats[i], slave_dbeats[i + 1]
        frag = time_stretch_beatmatch_fragment(master_audio, m_cur, m_next, s_cur, s_next)
        time_stretched_master_fadeout_audio_fragments.append(frag)

    # ------ Adding the last part ------ (tail fragment is the same operation)
    m_cur, m_next = master_dbeats[-1], len(master_audio)
    s_cur, s_next = slave_dbeats[-1], len(slave_audio)
    tail = time_stretch_beatmatch_fragment(master_audio, m_cur, m_next, s_cur, s_next)
    time_stretched_master_fadeout_audio_fragments.append(tail)

    # putting time_stretched_master_fadeout_audio_fragments together
    master_beatmatched_to_slave_audio = np.concatenate(time_stretched_master_fadeout_audio_fragments)
    # must be same length: master_beatmatched_to_slave_audio, slave_audio
    return master_beatmatched_to_slave_audio, slave_audio


def crop_audio_and_dbeats(song, start_dbeat, end_dbeat):
    audio = song.audio
    song_dbeats = song.get_downbeats()
    len_dbeats = len(song_dbeats)

    # Supporting negative indexing
    if start_dbeat < 0:
        start_dbeat = len_dbeats + start_dbeat
    if end_dbeat < 0:
        end_dbeat = len_dbeats + end_dbeat

    if start_dbeat >= len_dbeats or end_dbeat >= len_dbeats:  # or start_dbeat >= end_dbeat:
        raise Exception(f"Given start_dbeat({start_dbeat}) and/or end_dbeat({end_dbeat}) are not compatible.")
    
    start_dbeat_value = song_dbeats[start_dbeat]
    audio_start_idx, audio_end_idx = song_dbeats[start_dbeat], song_dbeats[end_dbeat]
    cropped_audio = audio[audio_start_idx: audio_end_idx]
    cropped_dbeats = song_dbeats[start_dbeat:end_dbeat] - start_dbeat_value

    new_song = Song()
    new_song.audio = cropped_audio
    new_song.downbeats = cropped_dbeats
    new_song.sample_rate = song.sample_rate
    new_song.num_channels = song.num_channels
    return new_song
    
def crossfade(master_song, slave_song, len_crossfade=8, len_time_stretch=8, settings=None):
    """Build a beat-matched crossfade between ``master_song`` and ``slave_song``.

    ``settings`` is a ``config.CrossfadeSettings``; lengths default to 8 bars.
    """
    if settings is None:
        settings = config.CrossfadeSettings(len_crossfade=len_crossfade,
                                           len_time_stretch=len_time_stretch)
    # Settings are the source of truth for the lengths (whether passed explicitly or
    # built above) - the function args are just convenient defaults.
    len_crossfade = settings.len_crossfade
    len_time_stretch = settings.len_time_stretch

    # We are getting the required song partitions and their respective dbeats from SongPartition class
    master_p_audio = master_song.audio
    master_p_dbeats = master_song.get_downbeats()
    slave_p_audio = slave_song.audio
    slave_p_dbeats = slave_song.get_downbeats()

    # calculate the factor of time stretching according to first
    # downbeat difference of master and slaves in crossfade
    crossfade_master_first_dbeat_diff = master_p_dbeats[(-1 * len_crossfade) + 1] - master_p_dbeats[-1 * len_crossfade]
    crossfade_slave_first_dbeat_diff = slave_p_dbeats[1] - slave_p_dbeats[0]
    ts_final_factor = crossfade_master_first_dbeat_diff / crossfade_slave_first_dbeat_diff

    # -- TIME STRETCHING --

    ts_dbeat_start = -1 * (len_crossfade + len_time_stretch)
    ts_dbeat_end = (-1 * len_crossfade) + 1
    ts_song = Song()
    ts_song.audio, ts_song.downbeats = master_p_audio, master_p_dbeats
    ts_cropped_song = crop_audio_and_dbeats(ts_song, ts_dbeat_start, ts_dbeat_end)
    
    time_stretch_audio = time_stretch_gradually_in_downbeats(ts_cropped_song, ts_final_factor)
    ts_start_idx = master_p_dbeats[ts_dbeat_start]

    # -- END TIME STRETCHING --

    # -- CROSSFADING --

    master_dbeats_start = len(master_p_dbeats) - len_crossfade - 1
    master_dbeats_end = len(master_p_dbeats) - 1
    master_fadeout_song = Song()
    master_fadeout_song.audio, master_fadeout_song.downbeats = master_p_audio, master_p_dbeats
    master_fadeout_cropped_song = crop_audio_and_dbeats(master_fadeout_song,
                                                                          master_dbeats_start,
                                                                          master_dbeats_end)
    slave_dbeats_start = 0
    slave_dbeats_end = len_crossfade
    slave_fadein_song = Song()
    slave_fadein_song.audio, slave_fadein_song.downbeats = slave_p_audio, slave_p_dbeats
    slave_fadein_cropped_song = crop_audio_and_dbeats(slave_fadein_song,
                                                    slave_dbeats_start,
                                                    slave_dbeats_end)


    master_fadeout_audio, slave_fadein_audio = beatmatch_to_slave(master_fadeout_cropped_song, slave_fadein_cropped_song)

    assert len(master_fadeout_audio) == len(slave_fadein_audio)

    # Sound Effects for Master & Slave: one 3-band DJ EQ crossfade
    fade_settings = settings.fade
    eq_settings = settings.eq
    sample_rate = master_song.sample_rate or slave_song.sample_rate or 44100

    from .utils import crossfade_eq
    crossfade_part_audio = crossfade_eq(
        master_fadeout_audio, slave_fadein_audio,
        eq_settings=eq_settings, sample_rate=sample_rate,
        master_start=fade_settings.master_start,
        slave_start=fade_settings.slave_start,
    )

    slave_fadein_end_idx = slave_p_dbeats[0] + crossfade_part_audio.shape[0]

    master_initial_audio = master_song.audio[:ts_start_idx]
    slave_remaining_audio = slave_song.audio[slave_fadein_end_idx:]

    # optional loudness balancing (replay-gain / manual offsets)
    from .utils import replay_gain_offset
    if settings.master_gain_db:
        master_initial_audio = replay_gain_offset(master_initial_audio, settings.master_gain_db)
        time_stretch_audio = replay_gain_offset(time_stretch_audio, settings.master_gain_db)
    if settings.slave_gain_db:
        slave_remaining_audio = replay_gain_offset(slave_remaining_audio, settings.slave_gain_db)


    crossfade_start_idx = ts_start_idx + time_stretch_audio.shape[0]
    crossfade_end_idx = crossfade_start_idx + crossfade_part_audio.shape[0]
    slave_start_idx = crossfade_end_idx       
     
    slave_remaining_song = crop_audio_and_dbeats(slave_fadein_song, slave_dbeats_end, -1)
    resulted_audio = np.concatenate([
        master_initial_audio,
        time_stretch_audio,
        crossfade_part_audio,
        slave_remaining_audio
    ])

    # click protection at the concat seams (length-neutral)
    from .utils import click_protect
    resulted_audio = click_protect(resulted_audio,
                                   [crossfade_start_idx, slave_start_idx],
                                   sample_rate=sample_rate)

    return Transition(
        audio=resulted_audio,
        master_initial_audio=master_song.audio[:ts_start_idx],
        slave_remaining_audio=slave_remaining_audio,
        slave_remaining_song=slave_remaining_song,
        time_stretch_audio=time_stretch_audio,
        crossfade_part_audio=crossfade_part_audio,
        slave_fadein_end_idx=slave_fadein_end_idx,
        time_stretch_start_idx=ts_start_idx,
        crossfade_start_idx=crossfade_start_idx,
        crossfade_end_idx=crossfade_end_idx,
        slave_start_idx=slave_start_idx,
        time_stretch_start_seconds=ts_start_idx / sample_rate,
        crossfade_start_seconds=crossfade_start_idx / sample_rate,
        crossfade_end_seconds=crossfade_end_idx / sample_rate,
        slave_start_seconds=slave_start_idx / sample_rate,
        slave_fadein_end_seconds=slave_fadein_end_idx / sample_rate,
        len_crossfade=len_crossfade,
        len_time_stretch=len_time_stretch,
    )



def crossfade_multiple(song_list, len_crossfade=8, len_time_stretch=8, settings=None):
    """Crossfade through 3+ songs, chaining each transition's tail.

    ``settings`` may be a shared ``config.CrossfadeSettings``; otherwise one is
    built from the length arguments.
    """
    if len(song_list) < 3:
        raise ValueError('crossfade_multiple needs at least 3 songs')
    if settings is None:
        settings = config.CrossfadeSettings(len_crossfade=len_crossfade,
                                           len_time_stretch=len_time_stretch)
    len_crossfade = settings.len_crossfade
    len_time_stretch = settings.len_time_stretch

    output_list = []
    mark_indices = []
    def append_to_output(part):
        output_list.append(part)
        a = 0
        for _ in output_list:
            a += len(_)
        mark_indices.append(a)

    master_song, slave_song, *other_songs = song_list

    cf = crossfade(master_song, slave_song, settings=settings)

    append_to_output(cf.master_initial_audio)
    append_to_output(cf.time_stretch_audio)
    append_to_output(cf.crossfade_part_audio)

    next_master_song = cf.slave_remaining_song
    next_cf = None
    for next_slave_song in other_songs:
        next_cf = crossfade(next_master_song, next_slave_song, settings=settings)

        append_to_output(next_cf.master_initial_audio)
        append_to_output(next_cf.time_stretch_audio)
        append_to_output(next_cf.crossfade_part_audio)

        next_master_song = next_cf.slave_remaining_song

    append_to_output(next_cf.slave_remaining_audio)

    full_audio = np.concatenate(output_list)

    return MultiTransition(full_transition=full_audio,
                          transition_indices=mark_indices)    