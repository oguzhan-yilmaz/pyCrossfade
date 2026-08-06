import numpy as np
import madmom
from . import utils
import os
from . import config


class Song():
    def __init__(self, filepath=None, audio_settings=None, beat_settings=None):
        self.filepath = filepath
        self.audio = None
        self.sample_rate = None
        self.num_channels = None
        self.beats = None
        self.downbeats = None
        self.duration_seconds = None
        self.replay_gain = None
        self.attributes = {}
        self.audio_settings = audio_settings or config.AudioSettings()
        self.beat_settings = beat_settings or config.BeatSettings()

        if filepath is not None:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Song file does not exist: {filepath}")
            self.song_name, self.song_format = self.get_song_name_and_format()
            self.load_song_audio()
            self.load_beats()
            self.populate_attributes()



    def populate_attributes(self):
        self.attributes = {
            "File": self.filepath,
            "Name": self.song_name,
            "Format": self.song_format,
            "Downbeats/Bars": len(self.get_downbeats()),
            "Beats": len(self.beats),
            "Duration": self.get_duration(),
            "DurationSeconds": int(self.duration_seconds),
            "SampleRate": self.sample_rate,
        }
        
        
    def extract(self):
        result = utils.music_extractor(self)
        utils.print_dict_as_table(result, header_key="Extractor Attribute", header_value="Value")

    def extract_replay_gain(self):
        """Compute and store the song's replay gain (dB) via Essentia."""
        from essentia.standard import MusicExtractor
        features, _ = MusicExtractor()(self.filepath)
        self.replay_gain = float(features['metadata.audio_properties.replay_gain'])
        return self.replay_gain

    def print_attribute_table(self, print_header=True):
        utils.print_dict_as_table(self.attributes, header_key="Attribute", header_value="Value", print_header=print_header)

    def __str__(self):
        return f"{self.song_name}.{self.song_format} :: {self.filepath}"
    
    
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
        
    def get_duration(self):
        return f'{int(self.duration_seconds//60)}:{round(self.duration_seconds%60)}'
        
    def load_song_audio(self):
        audio, sample_rate, num_channels = utils.load_audio(self.filepath)
        self.audio = audio
        self.sample_rate = self.audio_settings.sample_rate or sample_rate
        self.num_channels = self.audio_settings.num_channels or num_channels
        # duration is frames / sample rate regardless of channel count
        self.duration_seconds = self.audio.shape[0] / self.sample_rate
    
    def get_song_name_and_format(self):
        """Return ``(song_name, song_format)`` from a filepath.

        Robust to dots in the filename and Windows separators: the extension is
        taken from the last suffix, the rest becomes the name.
        """
        import os
        basename = os.path.basename(self.filepath)
        if '.' not in basename:
            return basename, ''
        name, _, fmt = basename.rpartition('.')
        return name, fmt

    def annotate_beats(self, output_filepath):
        bs = self.beat_settings
        downbeats_proc = madmom.features.DBNDownBeatTrackingProcessor(
            beats_per_bar=list(bs.beats_per_bar), fps=bs.fps)
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
        annotations_folder_name = self.beat_settings.annotations_directory
        utils.create_annotations_folder(annotations_folder_name)

        annotation_beats_path = utils.path_to_annotation_file(annotations_folder_name, self.song_name)

        if os.path.exists(annotation_beats_path):
            self.beats = np.loadtxt(annotation_beats_path)
        else:
            # there is no beats annotation - create it, then reload from disk.
            self.annotate_beats(annotation_beats_path)
            if not os.path.exists(annotation_beats_path):
                raise IOError(f"Failed to write beat annotations to {annotation_beats_path}")
            self.load_beats()