# Scripted Usage (deprecated)

## Installation

### Dependencies

This project requires *libsndfile*, *rubberband-cli*, *ffmpeg* to be installed on the system to work.


```bash
apt-get update && apt-get install -y libsndfile1 rubberband-cli ffmpeg
```

```bash
brew install libsndfile ffmpeg rubberband
```

-----

### Python Dependencies

#### Python Version

`madmom` package supports up to python 3.8, it's recommended to is this version. 


#### Installation

To install the projects dependencies run:

```bash
pip install -r requirements.txt
```

*!* _if you get an error about `Cython` refer to [this tip.](https://github.com/oguzhan-yilmaz/pyCrossfade#a-note-on-the-python-dependencies)_

|Package|Used For|
|---|---|
|[Cython](https://github.com/cython/cython) | Required by _madmom_ package.|
|[Numpy](https://github.com/numpy/numpy)|Handling audio data.|
|[pyrubberband](https://github.com/bmcfee/pyrubberband)|Python wrapper for rubberband, a perfectly capable time stretcher & pitch shifter.|
|[yodel](https://github.com/rclement/yodel)|Audio frequency filtering capabilities.|
|[essentia](https://github.com/MTG/essentia)|Format resilient audio loading and it's [MIR](https://en.wikipedia.org/wiki/Music_information_retrieval) tools.  	    |
|[madmom](https://github.com/CPJKU/madmom)|_State of the art_ beat-tracking.|

#### A note on the Python dependencies
Installing `madmom` package alone, if `Cython` package is not installed before hand, can fail. To solve this problem, you can `pip install cython` before installing madmom package.


----
## Example Usage

#### Transitioning Between Two Songs

```python
from pycrossfade import Song, crossfade, save_audio
# creating master and slave songs
master_song = Song('/path/to/master_song.mp3')
slave_song = Song('/path/to/slave_song.mp3')
# creating crossfade with bpm matching
output_audio = crossfade(master_song, slave_song, len_crossfade=8, len_time_stretch=8)
# saving the output
save_audio(output_audio, '/path/to/save/mix.wav')
```

#### Transitioning Between Multiple Songs

```python
from pycrossfade import Song, crossfade_multiple, save_audio
# creating songs
song_list = [
  Song('/path/to/song_one.mp3'),
  Song('/path/to/song_two.mp3'),
  Song('/path/to/song_three.mp3'),
]
# creating crossfade with bpm matching
output_audio = crossfade_multiple(song_list, len_crossfade=16, len_time_stretch=8)
# saving the output
save_audio(output_audio, '/path/to/save/mix_multiple.wav')
```

#### Transitioning Between Songs On Specific Bars

```python
from pycrossfade import Song, crossfade_multiple, crop_audio_and_dbeats, import save_audio
# creating songs
song_one = Song('/path/to/song_one.mp3')
song_two = Song('/path/to/song_two.mp3')
song_three = Song('/path/to/song_three.mp3')

song_list = [
    crop_audio_and_dbeats(song_one, 10, 35),
    crop_audio_and_dbeats(song_two, 30, 55),
    crop_audio_and_dbeats(song_three, 50, 75),
]
# creating crossfade with bpm matching
output_audio = crossfade_multiple(song_list, len_crossfade=8, len_time_stretch=8)
# saving the output
save_audio(output_audio, '/path/to/save/mix_multiple_specific_bars.wav')
```
