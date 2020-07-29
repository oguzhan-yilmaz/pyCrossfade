# pyCrossfade
[Projects Goal]
pyCrossfade is born out of a personal effort to create a customizable and beat-matched crossfade functionality. 


## Installation
---------

### Dependencies

This project requires *libsndfile*, *rubberband-cli*, *ffmpeg* to be installed on the system to work.

### Linux

```bash
apt-get update && apt-get install -y libsndfile1 rubberband-cli ffmpeg
```

### OSX


##### libsndfile
```bash
brew install libsndfile
```
##### ffmpeg
```bash
brew install ffmpeg
```

##### rubberband
```bash
brew install rubberband
```
-----

### Python Dependencies



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


### Installing  pyCrossfade
```bash
pip install pycrossfade
```
### About music used in demo





## About This Project
---------
This project's main goal is to create seamless crossfade transitions between music files. This requires some DJ'ing abilities such as _bpm changing_, _beat-matching_ and _equalizer manipulation_.


#### Some Definitions on Music Domain 
[Beat](https://en.wikipedia.org/wiki/Beat_(music))
In music and music theory, the beat is the basic unit of time, the pulse or regularly repeating event. 
The beat is often defined as the rhythm listeners would tap their toes to when listening to a piece of music. 


[Bar (Measure)](https://en.wikipedia.org/wiki/Bar_(music))
In musical notation, a bar (or measure) is a segment of time corresponding to a specific number of beats, usually 4.

[Downbeat](https://en.wikipedia.org/wiki/Beat_(music)#Downbeat_and_upbeat)
The downbeat is the first beat of the bar, i.e. number 1.


### pyCrossfade's Approach To Perfect Beat Matching
Human ear can catch minimal errors easily thus making beat-matching is extremely important for any transition. Beat-matching would be easy if every beat had regular timing, but producers are doing their best to [humanize their songs](https://www.izotope.com/en/learn/how-to-humanize-and-dehumanize-drums.html), not playing every beat in regular timing to get nonrobotic rhythms.

#### A Visual Explanation

Here, I cut two songs between their 30th and 50th downbeats, resulting in the same amount of downbeats.
![Escape.mp3 Downbeats](./assets/images/Escape-Downbeats.png)

Red lines are denoting every _bar_, or it's delimiter _downbeats_.

![Eyeillfals.mp3 Downbeats](./assets/images/Eyeillfals-Downbeats.png)

This is the second song with 20 bars.

![Escape.mp3 and  Downbeats](./assets/images/Eyeillfals-Escape-Downbeats.png)
> First song's waveform is blue and it's bars denoted with red lines. Second song is shown with colors of orange and green. 

When we put them on top of each other, we can see that their beats is not matched, resulting in distorted audio.


Even though they have same amount of bars, resulting plot shows that second song is shorter. This is beacuse they have different BPMs - or speeds.



### equalizer manipulation

### madmom beat tracking

### Approach master slave

### example code

### musics

jamendo - https://www.jamendo.com
 Milecklaster - Majed Salih https://www.jamendo.com/track/1765941/milecklaster

  Highway - Soundrider/Dope https://www.jamendo.com/track/1764828/highway

  Escape - Faylasuf ft. Peter Baran https://www.jamendo.com/track/1753056/faylasuf-escape-ft-peter-baran

Eyeillfals - Majed Salih https://www.jamendo.com/track/1754135/eyeillfals