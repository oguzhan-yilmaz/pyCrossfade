def time_stretch(audio, factor, sample_rate=44100):
    import pyrubberband as pyrb
    return pyrb.time_stretch(audio, sample_rate, factor)


def load_audio(filepath):
    # returns loaded mono audio.
    from essentia.standard import MonoLoader
    return MonoLoader(filename=filepath)()


def save_audio(audio, filename, file_format='wav', bit_rate=320):
    from essentia.standard import MonoWriter
    MonoWriter(filename=filename, bitrate=bit_rate, format=file_format)(audio)


def does_annotations_folder_exist(folder_name='pycrossfade_annotations'):
    from os.path import isdir
    return isdir(folder_name)


def create_annotations_folder(folder_name='pycrossfade_annotations'):
    from os import mkdir
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