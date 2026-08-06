"""Configuration and tunable settings for pyCrossfade.

Every magic number that once lived inline in the DSP code is now a setting.
Settings are plain dataclasses with sensible defaults; environment variables
can override the most commonly tweaked values. Instances can be passed
explicitly (e.g. a custom ``CrossfadeSettings``) or built from the
environment with ``from_env``.
"""
from dataclasses import dataclass, field
from os import environ
from typing import Optional, Tuple

# Legacy env-driven paths kept for the Docker workflow.
ANNOTATIONS_DIRECTORY = environ.get('ANNOTATIONS_DIRECTORY', 'pycrossfade_annotations')
BASE_AUDIO_DIRECTORY = environ.get('BASE_AUDIO_DIRECTORY', '')


@dataclass
class AudioSettings:
    """Audio I/O settings.

    ``sample_rate`` of ``None`` means "read the real sample rate from the file";
    ``num_channels`` of ``None`` means "keep the file's native channel count".
    """
    sample_rate: Optional[int] = None
    num_channels: Optional[int] = None
    bit_rate: int = 320


@dataclass
class BeatSettings:
    """Madmom beat-tracking settings."""
    beats_per_bar: Tuple[int, ...] = (4,)
    fps: int = 100
    annotations_directory: str = ANNOTATIONS_DIRECTORY


@dataclass
class FadeSettings:
    """Volume fade profile for the crossfade section.

    ``profile`` selects the perceived-level curve:
      - ``linear``       : straight gain ramp (loudest at the crossover point)
      - ``cosine``       : cos/sin equal-power-ish curve
      - ``equal_power``  : true equal-power curve (sum of squared gains ~ const)
    """
    profile: str = 'equal_power'
    master_start: float = 0.9
    master_end: float = 0.0
    slave_start: float = 0.1
    slave_end: float = 1.0


@dataclass
class EQSettings:
    """Three-band EQ used for the crossfade.

    Master fades out low+high shelves while slave fades them in; both get a
    mid-range dip at the overlap center for clarity (the classic DJ trick to
    avoid a muddy blend). ``gain_db`` caps how much the shelves boost/cut.
    """
    low_cutoff: float = 70.0
    mid_center: float = 1000.0
    high_cutoff: float = 13000.0
    q: float = 1.0 / (2 ** 0.5)
    gain_db: float = 26.0
    mid_dip_db: float = 6.0
    num_steps: int = 20


@dataclass
class CrossfadeSettings:
    """High-level crossfade parameters (lengths in bars)."""
    len_crossfade: int = 8
    len_time_stretch: int = 8
    mark_transitions: bool = False
    # optional manual loudness offsets (dB) applied before the crossfade
    master_gain_db: float = 0.0
    slave_gain_db: float = 0.0
    fade: FadeSettings = field(default_factory=FadeSettings)
    eq: EQSettings = field(default_factory=EQSettings)

    def __post_init__(self):
        if self.len_crossfade < 1:
            raise ValueError('len_crossfade must be >= 1')
        if self.len_time_stretch < 0:
            raise ValueError('len_time_stretch must be >= 0')
