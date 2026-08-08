from os.path import isdir
import pyrubberband as pyrb
import essentia
# disable essentia logs
essentia.log.infoActive = False 
essentia.log.warningActive = False 

from essentia.standard import MonoLoader, MonoWriter
from essentia.standard import MusicExtractor, AudioOnsetsMarker, YamlOutput, RhythmExtractor2013
from . import config
from pprint import pprint
import numpy as np

def onset_mark_at_indices(audio, indices,sample_rate=44100):
    marked_audio = None
    for idx in indices:
        marked_audio = add_beep_to_audio(audio, idx, beep_duration=0.03, beep_frequency=500, sample_rate=sample_rate)
    return marked_audio

def onset_mark_downbeats(song):
    dbeats = song.get_downbeats()
    return onset_mark_at_indices(song.audio, dbeats)

def add_beep_to_audio(audio, beep_index, beep_duration=0.1, beep_frequency=1000,
                      sample_rate=44100, amplitude=0.5):
    """Return a copy of ``audio`` with a short enveloped beep added at ``beep_index``.

    The input is never mutated. The beep gets a cosine fade-in/out envelope so
    it cannot click. Stereo arrays are handled per-channel.
    """
    n_samples = int(beep_duration * sample_rate)
    t = np.linspace(0.0, beep_duration, n_samples, endpoint=False)
    beep = np.sin(2 * np.pi * beep_frequency * t)

    # cosine envelope (10% rise/fall) to avoid clicks
    env = np.ones(n_samples)
    fade_n = max(1, int(0.1 * n_samples))
    env[:fade_n] *= 0.5 * (1.0 - np.cos(np.pi * np.arange(fade_n) / fade_n))
    env[-fade_n:] *= 0.5 * (1.0 - np.cos(np.pi * np.arange(fade_n)[::-1] / fade_n))
    beep = amplitude * beep * env

    # clip beep at the end of the audio
    end = min(beep_index + n_samples, audio.shape[0])
    if end <= beep_index:
        return audio.copy()

    modified = audio.copy()
    if audio.ndim == 1:
        modified[beep_index:end] += beep[:end - beep_index]
    else:
        modified[beep_index:end] += beep[:end - beep_index, None]
    return modified


# def save_music_extractor_results(song):
#     # from tempfile import TemporaryDirectory
#     # temp_dir = TemporaryDirectory()
#     results_file = f'music-extractor--{song.song_name}.json'
#     features, features_frames = MusicExtractor(lowlevelStats=['mean', 'stdev'],
#                                               rhythmStats=['mean', 'stdev'],
#                                               tonalStats=['mean', 'stdev'])(song.filepath)
#     features
#     YamlOutput(filename=results_file, format="json")(features)
#     return results_file    

def music_extractor(song):
    features, features_frames = MusicExtractor(lowlevelStats=['mean', 'stdev'],
                                              rhythmStats=['mean', 'stdev'],
                                              tonalStats=['mean', 'stdev'])(song.filepath)
    
    bit_rate = int(features['metadata.audio_properties.bit_rate'])
    duration_seconds = "{:.2f}".format( features['metadata.audio_properties.length'] )
    replay_gain = "{:.2f}".format( features['metadata.audio_properties.replay_gain'] )
    bpm = "{:.2f}".format( features['rhythm.bpm'] )
    sample_rate = round(features['metadata.audio_properties.sample_rate'])
    danceability = "{:.2f}/3.00".format( features['rhythm.danceability'])

    result = {
        "Filename": features['metadata.tags.file_name'],
        "Duration": song.get_duration(),
        "Duration (seconds)": duration_seconds,
        "BPM": bpm,
        "BPM (rounded)": round(features['rhythm.bpm']),
        "Sample Rate": sample_rate,
        "Danceability": danceability,
        f"Key/Scale estimation (edma)     [conf.: {'{:.2f}'.format(features['tonal.key_edma.strength'])}]":      features['tonal.key_edma.key'] + ' ' + features['tonal.key_edma.scale'],
        f"Key/Scale estimation (krumhansl)[conf.: {'{:.2f}'.format(features['tonal.key_krumhansl.strength'])}]": features['tonal.key_krumhansl.key'] + ' ' + features['tonal.key_krumhansl.scale'],
        f"Key/Scale estimation (temperley)[conf.: {'{:.2f}'.format(features['tonal.key_temperley.strength'])}]": features['tonal.key_temperley.key'] + ' ' + features['tonal.key_temperley.scale'],
        "Replay gain": replay_gain,
        "Audio bit rate": round(bit_rate),
        "Audio codec": features['metadata.audio_properties.codec'],
        "Number of channels (mono or stereo)": int(features['metadata.audio_properties.number_channels']),
        # "EBU128 integrated loudness": '{:.2f}'.format(features['lowlevel.loudness_ebu128.integrated']),
        # "EBU128 loudness range": '{:.2f}'.format(features['lowlevel.loudness_ebu128.loudness_range']),
        "MD5 hash for the encoded audio": features['metadata.audio_properties.md5_encoded'],

        
    }
    # print(a)
    return result 


def mark_downbeats_and_save(song):
    pass

def print_dict_as_table(dictionary, header_key=None, header_value=None, print_header=True):
    len_total = 50 + 62
    do_print_headers = print_header and (header_key and header_value)
    # print()
    if do_print_headers:
        key_str = header_key[:50]
        value_str = header_value[:62]
        print('{0: <50} {1: <62}'.format(key_str,value_str))
        print("-" * (len_total+1))  # Separator line
        
    # Print each key-value pair
    for key, value in dictionary.items():
        # Use str() to convert both key and value to strings
        # Truncate or pad to exact widths
        formatted_key = str(key)[:50].ljust(50)
        formatted_value = str(value)[:62].ljust(62)
        print(f"{formatted_key} {formatted_value}")

def time_stretch(audio, factor, sample_rate=44100):
    """Time-stretch audio by ``factor`` (channel-aware).

    Stereo arrays are stretched per-channel and re-stacked so pyrubberband never
    has to guess a channel layout.
    """
    if audio.ndim == 1:
        return pyrb.time_stretch(audio, sample_rate, factor)
    channels = [pyrb.time_stretch(audio[:, ch], sample_rate, factor)
                for ch in range(audio.shape[1])]
    return np.stack(channels, axis=1)


def load_audio(filepath):
    """Load audio (mono or stereo) and return ``(audio, sample_rate, num_channels)``.

    ``audio`` keeps the file's native channel layout; ``sample_rate`` is the
    file's real rate (no more hardcoded 44100).
    """
    from essentia.standard import AudioLoader
    result = AudioLoader(filename=filepath)()
    audio, sample_rate, num_channels = result[0], result[1], result[2]
    return audio, int(sample_rate), int(num_channels)


# Backward-compatible single-return wrapper for the deprecated scripted API.
def load_audio_mono(filepath):
    audio, _, _ = load_audio(filepath)
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    return audio


def save_audio(audio, filename, file_format='wav', bit_rate=320):
    """Save audio as mono or stereo depending on ``audio``'s shape."""
    from essentia.standard import AudioWriter
    AudioWriter(filename=filename, bitrate=bit_rate, format=file_format)(audio)



def click_protect(audio, boundary_indices, sample_rate=44100, fade_ms=3):
    """Apply short cosine fade-out/fade-in at splice boundaries to kill clicks.

    ``boundary_indices`` are the frame indices where segments were concatenated;
    a few milliseconds before/after each boundary is faded so the seam doesn't
    click. Returns a new array; the input is never mutated.
    """
    import numpy as np
    n = max(1, int(fade_ms / 1000.0 * sample_rate))
    out = audio.copy()
    for idx in boundary_indices:
        if idx <= 0 or idx >= audio.shape[0]:
            continue
        # fade-out the tail of the previous segment
        lo, hi = max(0, idx - n), idx
        fade_out = np.linspace(1.0, 0.0, hi - lo)
        if audio.ndim == 1:
            out[lo:hi] *= fade_out
        else:
            out[lo:hi] *= fade_out[:, None]
        # fade-in the head of the next segment
        lo2, hi2 = idx, min(audio.shape[0], idx + n)
        fade_in = np.linspace(0.0, 1.0, hi2 - lo2)
        if audio.ndim == 1:
            out[lo2:hi2] *= fade_in
        else:
            out[lo2:hi2] *= fade_in[:, None]
    return out


def _band_filter_stepped(audio, band, gains, eq_settings, sample_rate):
    """Filter ``audio`` through one band whose gain ramps per step.

    ``band`` is 'low_shelf', 'high_shelf' or 'peaking'. Gains are in dB;
    filter state (``zi``) is carried between steps to avoid zipper noise.
    """
    from yodel.filter import Biquad
    from scipy.signal import lfilter
    import numpy as np

    num_steps = len(gains)
    length = audio.shape[0]
    output = np.zeros(audio.shape, dtype=audio.dtype)
    zi = None
    for i in range(num_steps):
        start = int(i / float(num_steps) * length)
        end = int((i + 1) / float(num_steps) * length)
        if end <= start:
            continue
        f = Biquad()
        if band == 'low_shelf':
            f.low_shelf(sample_rate, eq_settings.low_cutoff, eq_settings.q, gains[i])
        elif band == 'high_shelf':
            f.high_shelf(sample_rate, eq_settings.high_cutoff, eq_settings.q, gains[i])
        elif band == 'peaking':
            f.peak(sample_rate, eq_settings.mid_center, eq_settings.q, gains[i])
        else:
            raise ValueError('Unknown band: ' + band)
        b = f._b_coeffs
        a = f._a_coeffs
        a[0] = 1.0  # yodel leaves a[0] != 1 after normalization
        # scipy.signal.lfilter only returns the (y, zf) tuple when a non-None
        # initial state is passed. Seed zero state on the first step so filter state
        # can be carried across steps (avoids zipper noise).
        n_state = max(len(a), len(b)) - 1
        if audio.ndim == 1:
            if zi is None:
                zi = np.zeros(n_state)
            y, zi = lfilter(b, a, audio[start:end], zi=zi)
            output[start:end] = y
        else:
            if zi is None:
                zi = [np.zeros(n_state) for _ in range(audio.shape[1])]
            new_zi = []
            for ch in range(audio.shape[1]):
                y, zi_ch = lfilter(b, a, audio[start:end, ch], zi=zi[ch])
                output[start:end, ch] = y
                new_zi.append(zi_ch)
            zi = new_zi
    return output


def crossfade_eq(master_audio, slave_audio, eq_settings=None, sample_rate=44100,
                 master_start=0.9, slave_start=0.1):
    """Combine master-fadeout + slave-fadein with a 3-band DJ crossfade EQ.

    Master shelves low+high down from ``master_start`` to silence; slave shelves
    low+high up from ``slave_start`` to full; *both* get a mid-range dip at the
    overlap center for clarity. The gain curves are smoothed per step (no clicks).
    """
    import numpy as np
    if eq_settings is None:
        eq_settings = config.EQSettings()

    num_steps = max(2, eq_settings.num_steps)
    t = np.linspace(0.0, 1.0, num_steps)

    master_level = master_start * (1.0 - t)
    slave_level = slave_start + (1.0 - slave_start) * t
    mid_dip = -eq_settings.mid_dip_db * np.sin(np.pi * t)

    master_band_gain = -eq_settings.gain_db * (1.0 - master_level)
    slave_band_gain = -eq_settings.gain_db * (1.0 - slave_level)

    master_eq = _band_filter_stepped(master_audio, 'low_shelf', master_band_gain, eq_settings, sample_rate)
    master_eq = _band_filter_stepped(master_eq, 'high_shelf', master_band_gain, eq_settings, sample_rate)
    master_eq = _band_filter_stepped(master_eq, 'peaking', mid_dip, eq_settings, sample_rate)

    slave_eq = _band_filter_stepped(slave_audio, 'low_shelf', slave_band_gain, eq_settings, sample_rate)
    slave_eq = _band_filter_stepped(slave_eq, 'high_shelf', slave_band_gain, eq_settings, sample_rate)
    slave_eq = _band_filter_stepped(slave_eq, 'peaking', mid_dip, eq_settings, sample_rate)

    return slave_eq + master_eq


def replay_gain_offset(audio, gain_db, sample_rate=44100, num_channels=None):
    """Apply a replay-gain offset (in dB) to the whole audio array.

    ``gain_db`` is the replay gain value Essentia reports (e.g. -10.46). A
    positive offset boosts; the gain is applied as a linear multiplier so the
    relative mix stays intact. Returns a new array; never mutates.
    """
    import numpy as np
    factor = 10.0 ** (gain_db / 20.0)
    return audio * factor


def does_annotations_folder_exist(folder_name=False):
    if not folder_name:
        folder_name = config.ANNOTATIONS_DIRECTORY
    return isdir(folder_name)


def create_annotations_folder(folder_name=False):
    
    from os import mkdir
    if not folder_name:
        folder_name = config.ANNOTATIONS_DIRECTORY
    if not does_annotations_folder_exist(folder_name):
        mkdir(folder_name)
        return True
    return False


def path_to_annotation_file(annt_folder_name, file_name, file_format='txt'):
    from os.path import join
    return join(annt_folder_name, file_name + '.' + file_format)    


def linear_fade_volume(audio, start_volume=0.0, end_volume=1.0, profile='linear'):
    """Apply a volume fade from ``start_volume`` to ``end_volume``.

    ``profile`` selects the gain curve: 'linear', 'cosine' or 'equal_power'.
    The returned array is a new array; the input is never mutated.
    """
    import numpy as np

    if start_volume == end_volume:
        return audio

    length = audio.shape[0]
    t = np.linspace(0.0, 1.0, length)
    if profile == 'linear':
        gains = np.linspace(start_volume, end_volume, length)
    elif profile == 'cosine':
        gains = start_volume + (end_volume - start_volume) * 0.5 * (1.0 - np.cos(np.pi * t))
    elif profile == 'equal_power':
        gains = np.sqrt(np.linspace(start_volume ** 2, end_volume ** 2, length))
    else:
        raise ValueError(f'Unknown fade profile: {profile}')

    if audio.ndim == 1:
        return audio * gains
    # stereo (N, 2) - broadcast the gain profile over channels
    return audio * gains[:, None]


def linear_fade_filter(audio, filter_type, start_volume=0.0, end_volume=1.0,
                       sample_rate=44100, eq_settings=None):
    """Shelf a low/high band from ``start_volume`` to ``end_volume``.

    Unlike the original, the filter coefficients are rebuilt per step from the
    settings (no hardcoded magic numbers, no reaching into ``_b_coeffs``) and
    filter state is carried between steps via ``zi`` to avoid zipper noise.
    """
    from yodel.filter import Biquad
    import numpy as np
    from scipy.signal import lfilter

    if start_volume == end_volume:
        return audio

    if eq_settings is None:
        eq_settings = config.EQSettings()

    num_steps = max(1, eq_settings.num_steps)
    length = audio.shape[0]
    profile = np.linspace(start_volume, end_volume, num_steps)
    output_audio = np.zeros(audio.shape, dtype=audio.dtype)

    # per-channel filter state so stereo isn't cross-contaminated
    zi = None
    for i in range(num_steps):
        start_idx = int((i / float(num_steps)) * length)
        end_idx = int(((i + 1) / float(num_steps)) * length)
        if end_idx <= start_idx:
            continue

        # gain maps 0..1 -> full shelf (gain_db) .. 0
        gain = -eq_settings.gain_db * (1.0 - profile[i])
        bquad_filter = Biquad()
        if filter_type == 'low_shelf':
            bquad_filter.low_shelf(sample_rate, eq_settings.low_cutoff, eq_settings.q, gain)
        elif filter_type == 'high_shelf':
            bquad_filter.high_shelf(sample_rate, eq_settings.high_cutoff, eq_settings.q, gain)
        else:
            raise ValueError('Unknown filter type: ' + filter_type)

        b = bquad_filter._b_coeffs
        a = bquad_filter._a_coeffs
        a[0] = 1.0  # yodel normalizes coefficients but leaves a[0] != 1

        # scipy.signal.lfilter only returns the (y, zf) tuple when a non-None
        # initial state is passed. Seed zero state on the first step so filter state
        # can be carried across steps (avoids zipper noise).
        n_state = max(len(a), len(b)) - 1
        if audio.ndim == 1:
            if zi is None:
                zi = np.zeros(n_state)
            y, zi = lfilter(b, a, audio[start_idx:end_idx], zi=zi)
            output_audio[start_idx:end_idx] = y
        else:
            # stereo: run each channel with its own state
            if zi is None:
                zi = [np.zeros(n_state) for _ in range(audio.shape[1])]
            new_zi = []
            for ch in range(audio.shape[1]):
                y, zi_ch = lfilter(b, a, audio[start_idx:end_idx, ch], zi=zi[ch])
                output_audio[start_idx:end_idx, ch] = y
                new_zi.append(zi_ch)
            zi = new_zi

    return output_audio