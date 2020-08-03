import numpy as np
from .utils import *
from .song import Song

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
    return new_song


def time_stretch_gradually_in_downbeats(song, final_factor):
    # Since we are time stretching *in-between* down beats, dbeat array has to
    # include the +1 dbeat in itself
    if final_factor == 1:
        return audio

    audio = song.audio
    dbeats = song.get_downbeats()

    ts_factor_step_len = (final_factor - 1.0) / (len(dbeats) - 1)

    ts_factors = np.arange(1.0, final_factor, ts_factor_step_len)[1:]

    time_stretched_audio_slices = []
    for i in range(len(ts_factors)):
        # get the current factor
        factor = ts_factors[i]
        slice = time_stretch(audio[dbeats[i]:dbeats[i + 1]], factor)
        time_stretched_audio_slices.append(slice)

    output = np.concatenate(time_stretched_audio_slices)
    return output

def beatmatch_to_slave(master_song, slave_song):
    master_audio = master_song.audio
    master_dbeats = master_song.get_downbeats()
    slave_audio = slave_song.audio
    slave_dbeats= slave_song.get_downbeats()

    if len(master_dbeats) != len(slave_dbeats):
        raise Exception(f"master_dbeats({len(master_dbeats)}) and slave_dbeats({len(slave_dbeats)}) is not same length")

    len_beatmatch_dbeats = len(master_dbeats)


    
    # Time stretching between every dbeat, according their respective time difference
    time_stretched_master_fadeout_audio_fragments = []
    master_next_idx = None
    for i in range(len_beatmatch_dbeats - 1):
        # these are dbeats
        master_cur_idx, master_next_idx = master_dbeats[i], master_dbeats[i + 1]
        slave_cur_idx, slave_next_idx = slave_dbeats[i], slave_dbeats[i + 1]

        # getting the next_dbeat_index - current_dbeat_index difference
        master_dbeat_diff_idx = master_next_idx - master_cur_idx
        slave_dbeat_diff_idx = slave_next_idx - slave_cur_idx

        # calculating the time stretch factor
        ts_factor = master_dbeat_diff_idx / slave_dbeat_diff_idx

        # getting the masters audio fragments for that downbeat indices
        master_audio_frag = master_audio[master_cur_idx:master_next_idx]

        ts_maf = time_stretch(master_audio_frag, ts_factor)

        # when time stretching with floating point factors, created audio can be more or less in length
        # so we are fixing that here. Its usually 20-50 frame indices difference, so its inaudible to cut it off
        if len(ts_maf) > slave_dbeat_diff_idx:
            ts_maf = ts_maf[:slave_dbeat_diff_idx]
        elif len(ts_maf) < slave_dbeat_diff_idx:
            ts_maf = np.concatenate((ts_maf, np.zeros(slave_dbeat_diff_idx - len(ts_maf))))

        # adding the current dbeats time stretched master audio fragment to the list
        # we will add them together later.
        time_stretched_master_fadeout_audio_fragments.append(ts_maf)

    # ------ Adding the last part ------
    master_cur_idx, master_next_idx = master_dbeats[-1], len(master_audio)
    slave_cur_idx, slave_next_idx = slave_dbeats[-1], len(slave_audio)
    # getting the next_dbeat_index - current_dbeat_index difference
    master_dbeat_diff_idx = master_next_idx - master_cur_idx
    slave_dbeat_diff_idx = slave_next_idx - slave_cur_idx
    # calculating the time stretch factor
    ts_factor = master_dbeat_diff_idx / slave_dbeat_diff_idx

    # getting the masters audio fragments for that downbeat indices
    master_audio_frag = master_audio[master_cur_idx:master_next_idx]

    ts_maf = time_stretch(master_audio_frag, ts_factor)


    # when time stretching with floating point factors, created audio can be more or less in length
    # so we are fixing that here. Its usually 20-50 frame indices difference, so its inaudible to cut it off
    if len(ts_maf) > slave_dbeat_diff_idx:
        ts_maf = ts_maf[:slave_dbeat_diff_idx]
    elif len(ts_maf) < slave_dbeat_diff_idx:
        ts_maf = np.concatenate((ts_maf, np.zeros(slave_dbeat_diff_idx - len(ts_maf))))

    # adding the current dbeats time stretched master audio fragment to the list
    # we will add them together later.
    time_stretched_master_fadeout_audio_fragments.append(ts_maf)

    # ------ END Adding the last part ------

    # putting time_stretched_master_fadeout_audio_fragments together
    master_beatmatched_to_slave_audio = np.concatenate(time_stretched_master_fadeout_audio_fragments)
    # must be same length: master_beatmatched_to_slave_audio, slave_audio
    return master_beatmatched_to_slave_audio, slave_audio




def crossfade(master_song, slave_song, len_crossfade, len_time_stretch, return_audio=True):
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

    # Sound Effects for Master
    new_master_fadedout = linear_fade_volume(master_fadeout_audio, start_volume=0.9, end_volume=0.0)
    new_master_fadedout = linear_fade_filter(new_master_fadedout, 'low_shelf', start_volume=0.9, end_volume=0.0)
    new_master_fadedout = linear_fade_filter(new_master_fadedout, 'high_shelf', start_volume=0.9, end_volume=0.0)

    # Sound Effects for Slave
    new_slave_fadedin = linear_fade_volume(slave_fadein_audio, start_volume=0.1, end_volume=1.0)
    new_slave_fadedin = linear_fade_filter(new_slave_fadedin, 'low_shelf', start_volume=0.0, end_volume=1.0)
    new_slave_fadedin = linear_fade_filter(new_slave_fadedin, 'high_shelf', start_volume=0.0, end_volume=1.0)

    crossfade_audio = new_slave_fadedin + new_master_fadedout

    slave_fadein_end_idx = slave_p_dbeats[0] + len(new_slave_fadedin)


    if return_audio:
        return np.concatenate([
            master_song.audio[:ts_start_idx],
            time_stretch_audio,
            crossfade_audio,
            slave_song.audio[slave_fadein_end_idx:]
        ])
    else:
        return {'time_stretch_audio': time_stretch_audio,
                'crossfade_audio': crossfade_audio,
                'len_crossfade': len_crossfade,
                'len_time_stretch': len_time_stretch,
                'ts_start_idx': ts_start_idx,
                'slave_fadein_end_idx': slave_fadein_end_idx}


def crossfade_multiple(song_list, len_crossfade, len_time_stretch):
    import numpy as np
    master_song = song_list[0]
    slave_song = song_list[1]
    output_list = []

    # crossfade and crossfade-before
    cf_before = None
    cf = None

    # crossfade between partitions
    for i in range(len(song_list) - 1):
        master_song = song_list[i]
        slave_song = song_list[i + 1]
        cf_before = cf
        cf = crossfade(master_song, slave_song, len_crossfade, len_time_stretch, return_audio=False)

        if i == 0:
            # if its the first song on the list
            master_p_audio_start_idx = 0
            master_p_audio_end_idx = cf['ts_start_idx']

        else:
            # if its not
            master_p_audio_start_idx = cf_before['slave_fadein_end_idx']
            master_p_audio_end_idx = cf['ts_start_idx']

        master_audio = master_song.audio
        output_list.append(master_audio[master_p_audio_start_idx:master_p_audio_end_idx])
        output_list.append(cf['time_stretch_audio'])
        output_list.append(cf['crossfade_audio'])

    # adding the last part
    slave_audio = slave_song.audio
    output_list.append(slave_audio[cf['slave_fadein_end_idx']:])
    return np.concatenate(output_list)