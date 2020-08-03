import numpy as np
import madmom 
from . import utils
import os


class Song():
    def __init__(self, filepath=None):
        self.filepath = filepath
        self.audio = None
        self.sample_rate = 44100
        self.beats = None
        self.downbeats = None

        if filepath is not None:
            self.song_name, self.song_format = self.get_song_name_and_format()
            self.load_song_audio()
            self.load_beats()

    #def plot_downbeats(self, start_dbeat, end_dbeat, plot_name='', color='red'):
    #    import matplotlib.pyplot as plt
    #    plt.rcParams['figure.figsize'] = (20, 9) 
    #    dbeats = self.get_downbeats()
    #    start_idx, end_idx = dbeats[start_dbeat], dbeats[end_dbeat]
    #    selected_dbeats = dbeats[start_dbeat:end_dbeat+1] - start_idx
    #    plt.plot(self.audio[start_idx: end_idx])
    #    for dbeat in selected_dbeats:
    #        plt.axvline(dbeat, color=color)
    #    plt.title(plot_name)
    #    plotname = ''.join(plot_name.split(' '))
    #    plt.savefig(f'{plotname}.png')
        

    def load_song_audio(self):
        self.audio = utils.load_audio(self.filepath)

    def get_song_name_and_format(self):
        # returns ../song_name.song_format -> song_name and song_format
        return self.filepath.split('/')[-1].split('.')

    def annotate_beats(self, output_filepath):
        downbeats_proc = madmom.features.DBNDownBeatTrackingProcessor(beats_per_bar=[4], fps=100)
        activations = madmom.features.RNNDownBeatProcessor()(self.filepath)
        beats = downbeats_proc(activations)
        np.savetxt(output_filepath, beats, newline="\n")
        return beats

    def get_downbeats(self):
        if self.downbeats is not None:
            return self.downbeats

        beats = self.beats
        dbeats = []
        for beat_sec, beat_num in beats:
            if beat_num == 1:
                dbeats.append(beat_sec)
        dbeats_time_to_audio_index = np.array(dbeats, dtype=float) * self.sample_rate
        self.downbeats = np.array(dbeats_time_to_audio_index, dtype=int)
        return self.downbeats

    def load_beats(self):
        annotations_folder_name = 'pycrossfade_annotations'
        utils.create_annotations_folder(annotations_folder_name)

        annotation_beats_path = utils.path_to_annotation_file(annotations_folder_name, self.song_name)

        if os.path.exists(annotation_beats_path):
            self.beats = np.loadtxt(annotation_beats_path)
        else:
            # there is no beats annotation
            self.annotate_beats(annotation_beats_path)
            # log here
            self.load_beats()