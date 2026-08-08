#!/usr/bin/env python3
"""pyCrossfade SDK examples — crossfade options with commented parameters.

Run inside the Docker image (recommended) so madmom/essentia deps match production:

    docker run --rm -v "$PWD/audios:/app/audios" -v "$PWD/examples:/app/examples" \\
      --entrypoint python3 ghcr.io/oguzhan-yilmaz/pycrossfade:latest \\
      /app/examples/sdk.py

Or locally if the full dependency stack is installed.
"""

from pycrossfade import Song, crossfade, crossfade_multiple, save_audio, config
from pycrossfade import utils


def example_basic():
    """Minimal two-song crossfade with defaults."""
    master = Song("master.mp3")   # filepath; channels and sample rate come from the file
    slave = Song("slave.mp3")

    result = crossfade(master, slave)
    # result is a Transition dataclass; .audio is the full concatenated mix

    save_audio(result.audio, "basic_mix.wav")


def example_lengths():
    """Control time-stretch and crossfade regions (in bars)."""
    settings = config.CrossfadeSettings(
        len_time_stretch=4,   # bars: gradual master stretch before the blend
        len_crossfade=16,     # bars: EQ + volume overlap (must be >= 1)
    )

    master = Song("master.mp3")
    slave = Song("slave.mp3")
    result = crossfade(master, slave, settings=settings)

    save_audio(result.audio, "long_crossfade.wav")


def example_fade_profiles():
    """Volume curve during the crossfade: linear, cosine, or equal_power."""
    for profile in ("linear", "cosine", "equal_power"):
        settings = config.CrossfadeSettings(
            fade=config.FadeSettings(
                profile=profile,    # perceived loudness curve through the overlap
                master_start=0.9,     # master volume at crossfade start (0–1)
                master_end=0.0,       # master volume at crossfade end
                slave_start=0.1,      # slave volume at crossfade start
                slave_end=1.0,        # slave volume at crossfade end
            ),
        )
        master = Song("master.mp3")
        slave = Song("slave.mp3")
        result = crossfade(master, slave, settings=settings)
        save_audio(result.audio, f"mix_{profile}.wav")


def example_eq_tuning():
    """Three-band DJ EQ: shelf cutoffs, mid dip, and step count."""
    settings = config.CrossfadeSettings(
        eq=config.EQSettings(
            low_cutoff=70.0,      # Hz — low shelf corner
            mid_center=1000.0,    # Hz — mid dip center
            high_cutoff=13000.0,  # Hz — high shelf corner
            q=1.0 / (2 ** 0.5),   # filter Q for shelves
            gain_db=26.0,         # max shelf boost/cut during the blend
            mid_dip_db=6.0,       # both tracks dip mids at overlap center (clarity)
            num_steps=20,         # EQ interpolation steps across the crossfade
        ),
    )

    master = Song("master.mp3")
    slave = Song("slave.mp3")
    result = crossfade(master, slave, settings=settings)
    save_audio(result.audio, "eq_tuned_mix.wav")


def example_loudness_offsets():
    """Replay-gain-style dB offsets before blending."""
    settings = config.CrossfadeSettings(
        master_gain_db=-2.0,  # dB added to master before crossfade
        slave_gain_db=1.5,    # dB added to slave before crossfade
    )

    master = Song("master.mp3")
    slave = Song("slave.mp3")
    result = crossfade(master, slave, settings=settings)
    save_audio(result.audio, "gain_balanced_mix.wav")


def example_sample_rate():
    """Override processing sample rate (resample on load)."""
    audio_settings = config.AudioSettings(
        sample_rate=48000,    # Hz; None = use each file's native rate
        num_channels=None,    # None = keep native channel count (stereo preserved)
        bit_rate=320,         # used when writing compressed formats
    )

    master = Song("master.mp3", audio_settings=audio_settings)
    slave = Song("slave.mp3", audio_settings=audio_settings)

    result = crossfade(master, slave)
    save_audio(result.audio, "48k_mix.wav")


def example_mark_transitions():
    """Beeps at stretch start, crossfade start, and crossfade end."""
    settings = config.CrossfadeSettings(
        mark_transitions=True,  # flag stored on settings; apply beeps after crossfade
    )

    master = Song("master.mp3")
    slave = Song("slave.mp3")
    result = crossfade(master, slave, settings=settings)

    audio = result.audio
    if settings.mark_transitions:
        mark_indices = (
            result.time_stretch_start_idx,  # sample index where gradual stretch begins
            result.crossfade_start_idx,     # sample index where EQ blend begins
            result.crossfade_end_idx,       # sample index where slave is fully in
        )
        audio = utils.onset_mark_at_indices(audio, mark_indices)

    save_audio(audio, "marked_mix.wav")


def example_inspect_transition():
    """Read timing and component slices from the typed Transition result."""
    settings = config.CrossfadeSettings(len_crossfade=8, len_time_stretch=8)
    master = Song("master.mp3")
    slave = Song("slave.mp3")
    result = crossfade(master, slave, settings=settings)

    # Full mix and per-section audio (numpy arrays)
    _full = result.audio
    _master_head = result.master_initial_audio      # master before time-stretch
    _stretch_section = result.time_stretch_audio    # gradual stretch region
    _overlap = result.crossfade_part_audio          # EQ + volume overlap only
    _slave_tail = result.slave_remaining_audio      # slave after crossfade ends

    # Sample indices (for your own edits or visualization)
    print("time_stretch_start:", result.time_stretch_start_idx,
          f"({result.time_stretch_start_seconds:.2f}s)")
    print("crossfade_start:   ", result.crossfade_start_idx,
          f"({result.crossfade_start_seconds:.2f}s)")
    print("crossfade_end:     ", result.crossfade_end_idx,
          f"({result.crossfade_end_seconds:.2f}s)")

    # Legacy dict access still works
    assert result["audio"] is result.audio

    save_audio(result.audio, "inspected_mix.wav")


def example_full_recipe():
    """All major CrossfadeSettings knobs in one place."""
    settings = config.CrossfadeSettings(
        len_time_stretch=8,
        len_crossfade=8,
        mark_transitions=False,
        master_gain_db=0.0,
        slave_gain_db=0.0,
        fade=config.FadeSettings(profile="equal_power"),
        eq=config.EQSettings(mid_dip_db=6.0),
    )

    audio_settings = config.AudioSettings(sample_rate=None)  # native rate

    master = Song("master.mp3", audio_settings=audio_settings)
    slave = Song("slave.mp3", audio_settings=audio_settings)
    result = crossfade(master, slave, settings=settings)

    save_audio(result.audio, "full_recipe.wav")


def example_crossfade_many():
    """Chain three or more songs with shared settings."""
    settings = config.CrossfadeSettings(
        len_time_stretch=8,
        len_crossfade=8,
        fade=config.FadeSettings(profile="cosine"),
    )

    songs = [
        Song("track_a.mp3"),
        Song("track_b.mp3"),
        Song("track_c.mp3"),
    ]

    multi = crossfade_multiple(songs, settings=settings)
    # multi.full_transition — entire chained mix
    # multi.transition_indices — beep/mark sample indices for each join

    save_audio(multi.full_transition, "set_mix.wav")


if __name__ == "__main__":
    # Uncomment the example you want to run (requires master.mp3 / slave.mp3 in audios/).
    example_basic()
    # example_lengths()
    # example_fade_profiles()
    # example_eq_tuning()
    # example_loudness_offsets()
    # example_sample_rate()
    # example_mark_transitions()
    # example_inspect_transition()
    # example_full_recipe()
    # example_crossfade_many()
