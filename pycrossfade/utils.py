from os.path import isdir
import pyrubberband as pyrb
import essentia
# disable essentia logs
essentia.log.infoActive = False 
essentia.log.warningActive = False 

from essentia.standard import MonoLoader, MonoWriter
from essentia.standard import MusicExtractor, AudioOnsetsMarker, YamlOutput, RhythmExtractor2013
import cliconfig
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

def add_beep_to_audio(audio, beep_index, beep_duration=0.1, beep_frequency=1000, sample_rate=44100):
    """
    Add a beep sound to an existing audio array at a specific index.
    
    Parameters:
    - audio: Input audio numpy array
    - beep_index: Index where the beep should start
    - beep_duration: Duration of the beep in seconds (default 0.1s)
    - beep_frequency: Frequency of the beep in Hz (default 1000 Hz)
    - sample_rate: Audio sample rate (default 44100 Hz)
    
    Returns:
    - Modified audio array with beep added
    """
    # Create time array for the beep
    t = np.linspace(0, beep_duration, 
                    int(beep_duration * sample_rate), 
                    endpoint=False)
    
    # Generate sine wave for the beep
    beep = np.sin(2 * np.pi * beep_frequency * t)
    
    # Ensure beep doesn't exceed original audio length
    if beep_index + len(beep) > len(audio):
        beep = beep[:len(audio) - beep_index]
    
    # # Create a copy of the original audio to modify
    # modified_audio = audio.copy()
    
    # Add the beep to the audio at the specified index
    audio[beep_index:beep_index+len(beep)] += beep
    
    return audio


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
    return pyrb.time_stretch(audio, sample_rate, factor)


def load_audio(filepath):
    # returns loaded mono audio.
    return MonoLoader(filename=filepath)()


def save_audio(audio, filename, file_format='wav', bit_rate=320):
    MonoWriter(filename=filename, bitrate=bit_rate, format=file_format)(audio)



def does_annotations_folder_exist(folder_name=False):
    if not folder_name:
        folder_name = cliconfig.ANNOTATIONS_DIRECTORY
    return isdir(folder_name)


def create_annotations_folder(folder_name=False):
    
    from os import mkdir
    if not folder_name:
        folder_name = cliconfig.ANNOTATIONS_DIRECTORY
    if not does_annotations_folder_exist(folder_name):
        mkdir(folder_name)
        return True
    return False


def path_to_annotation_file(annt_folder_name, file_name, file_format='txt'):
    from os.path import join
    return join(annt_folder_name, file_name + '.' + file_format)    


def linear_fade_volume(audio, start_volume=0.0, end_volume=1.0):
    import numpy as np

    if start_volume == end_volume:
        return audio

    length = audio.size
    profile = np.sqrt(np.linspace(start_volume, end_volume, length))
    return audio * profile


def linear_fade_filter(audio, filter_type, start_volume=0.0, end_volume=1.0):
    from yodel.filter import Biquad
    import numpy as np
    from scipy.signal import lfilter

    if start_volume == end_volume:
        return audio

    SAMPLE_RATE = 44100
    LOW_CUTOFF = 70
    MID_CENTER = 1000
    HIGH_CUTOFF = 13000
    Q = 1.0 / np.sqrt(2)
    NUM_STEPS = 20 if start_volume != end_volume else 1

    bquad_filter = Biquad()
    length = audio.size  # Assumes mono audio

    profile = np.linspace(start_volume, end_volume, NUM_STEPS)
    output_audio = np.zeros(audio.shape)

    for i in range(NUM_STEPS):
        start_idx = int((i / float(NUM_STEPS)) * length)
        end_idx = int(((i + 1) / float(NUM_STEPS)) * length)
        if filter_type == 'low_shelf':
            bquad_filter.low_shelf(SAMPLE_RATE, LOW_CUTOFF, Q, -int(26 * (1.0 - profile[i])))
        elif filter_type == 'high_shelf':
            bquad_filter.high_shelf(SAMPLE_RATE, HIGH_CUTOFF, Q, -int(26 * (1.0 - profile[i])))
        else:
            raise Exception('Unknown filter type: ' + filter_type)
        # ~ bquad_filter.process(audio[start_idx : end_idx], output_audio[start_idx : end_idx]) # This was too slow, code beneath is faster!
        b = bquad_filter._b_coeffs
        a = bquad_filter._a_coeffs
        a[
            0] = 1.0  # Normalizing the coefficients is already done in the yodel object, but a[0] is never reset to 1.0 after division!
        output_audio[start_idx: end_idx] = lfilter(b, a, audio[start_idx: end_idx]).astype('float32')

    return output_audio