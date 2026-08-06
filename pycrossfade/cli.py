
import typer
from .song import Song
from . import utils
from typing_extensions import Annotated, Optional, List
import numpy as np
from . import transition
from . import config
from pprint import pprint
app = typer.Typer(
    no_args_is_help=True,
)

# git config --global user.name "Oguzhan Yilmaz"
# git config --global user.email "oguzhan@hepapi.com"



@app.command(no_args_is_help=True, short_help="Crossfade between two songs")
def crossfade(
        master_filepath: Annotated[str, typer.Argument(help="Filepath to Master song")],
        slave_filepath: Annotated[str, typer.Argument(help="Filepath to Slave song")],
        len_time_stretch: Annotated[ Optional[int], typer.Option('--len-time-stretch', '-t', help="Time-stretch length in bars")  ]=8,
        len_crossfade: Annotated[ Optional[int], typer.Option('--len-crossfade', '-c', help="Crossfade length in bars")  ]=8,
        output: Annotated[ Optional[str], typer.Option('--output', '-o', help="Save the output audio to") ] = "",
        verbose: Annotated[ Optional[bool], typer.Option('--verbose', '-v',help="Print details about the crossfade") ] = False,
        mark_transitions: Annotated[ Optional[bool], typer.Option('--mark-transitions',help="Play a beep sound at time-stretch, crossfade, and slave starts") ] = False,
        fade_profile: Annotated[ Optional[str], typer.Option('--fade-profile',help="Volume fade curve: linear, cosine, equal_power") ] = None,
        master_gain: Annotated[ Optional[float], typer.Option('--master-gain',help="Master loudness offset in dB (replay-gain style)") ] = 0.0,
        slave_gain: Annotated[ Optional[float], typer.Option('--slave-gain',help="Slave loudness offset in dB (replay-gain style)") ] = 0.0,
        sample_rate: Annotated[ Optional[int], typer.Option('--sample-rate',help="Override the output sample rate") ] = None,
    ):

    if len_crossfade < 1:
        raise typer.BadParameter("--len-crossfade must be >= 1")
    if len_time_stretch < 0:
        raise typer.BadParameter("--len-time-stretch must be >= 0")

    settings = config.CrossfadeSettings(
        len_crossfade=len_crossfade,
        len_time_stretch=len_time_stretch,
        mark_transitions=mark_transitions,
        master_gain_db=master_gain,
        slave_gain_db=slave_gain,
    )
    if fade_profile:
        settings.fade.profile = fade_profile
    audio_settings = config.AudioSettings(sample_rate=sample_rate) if sample_rate else None

    master_song = Song(config.BASE_AUDIO_DIRECTORY + master_filepath,
                       audio_settings=audio_settings)
    slave_song = Song(config.BASE_AUDIO_DIRECTORY + slave_filepath,
                      audio_settings=audio_settings)

    result = transition.crossfade(master_song, slave_song, settings=settings)

    if not output:
        output = f"crossfade-{master_song.song_name}---{slave_song.song_name}.wav"
    output = config.BASE_AUDIO_DIRECTORY + output

    audio = result.audio
    if mark_transitions:
        mark_indices = (result.time_stretch_start_idx,
                        result.crossfade_start_idx,
                        result.slave_start_idx)
        audio = utils.onset_mark_at_indices(audio, mark_indices)
    utils.save_audio(audio, output)
    if verbose:
        table = result.to_dict()
        table['saved_file'] = output
        for key in ('slave_remaining_song', 'time_stretch_audio',
                    'crossfade_part_audio', 'audio', 'slave_remaining_audio',
                    'master_initial_audio'):
            table.pop(key, None)
        utils.print_dict_as_table(table)
    else:
        print(f"Crossfade saved to {output}")

@app.command(no_args_is_help=True, short_help="Crossfade between min. of 3 songs")
def crossfade_many(
        song_filepaths: Annotated[  List[str], typer.Argument(help="Songs filepaths [Min 3] (seperated by spaces)")],
        len_time_stretch: Annotated[ Optional[int], typer.Option('--len-time-stretch', '-t',help="Time-stretch length in bars")]=8,
        len_crossfade: Annotated[ Optional[int], typer.Option('--len-crossfade', '-c',help="Crossfade length in bars")]=8,
        output: Annotated[ Optional[str], typer.Option('--output', '-o', help="Save the output audio to (song.wav)") ] = "",
        verbose: Annotated[ Optional[bool], typer.Option('--verbose', '-v',help="Print details about the crossfade") ] = False,
        mark_transitions: Annotated[ Optional[bool], typer.Option('--mark-transitions',help="Play a beep sound at time-stretch, crossfade, and slave starts") ] = False,
        fade_profile: Annotated[ Optional[str], typer.Option('--fade-profile',help="Volume fade curve: linear, cosine, equal_power") ] = None,
    ):

    if len(song_filepaths) < 3:
        raise typer.BadParameter("crossfade-many needs at least 3 song filepaths")
    if len_crossfade < 1:
        raise typer.BadParameter("--len-crossfade must be >= 1")
    if len_time_stretch < 0:
        raise typer.BadParameter("--len-time-stretch must be >= 0")

    settings = config.CrossfadeSettings(len_crossfade=len_crossfade,
                                       len_time_stretch=len_time_stretch,
                                       mark_transitions=mark_transitions)
    if fade_profile:
        settings.fade.profile = fade_profile

    song_list = [Song(config.BASE_AUDIO_DIRECTORY + fp) for fp in song_filepaths]

    multi_transition = transition.crossfade_multiple(song_list, settings=settings)

    output_audio = multi_transition.full_transition

    if mark_transitions:
        output_audio = utils.onset_mark_at_indices(output_audio,
                                                   multi_transition.transition_indices)

    if not output:
        output = f"crossfadeMany-{'-'.join(s.song_name for s in song_list)}.wav"
    output = config.BASE_AUDIO_DIRECTORY + output

    utils.save_audio(output_audio, output)

    if verbose:
        utils.print_dict_as_table({
            "Songs": len(song_list),
            "Transition marks": ", ".join(str(i) for i in multi_transition.transition_indices),
            "Saved file": output,
        })
    else:
        print(f"Crossfade saved to {output}")
        
    
    
@app.command(no_args_is_help=True, short_help="Process song and print metadata")
def song(filepath: Annotated[str, typer.Argument(help="Filepath to song")]):
    # print(f"filepath={filepath}")
    filepath = config.BASE_AUDIO_DIRECTORY+filepath

    print("> Processing audio...")
    s = Song(filepath)
    print("> Audio loaded!")
    s.print_attribute_table()


@app.command(no_args_is_help=True, short_help="Extract BPM, ReplayGain, Key/Scale etc.")
def extract(
        filepath: Annotated[str, typer.Argument(help="Filepath to song")], 
        # output: Annotated[Optional[bool], typer.Option('--output', '-o')] = False,
    ):
    filepath = config.BASE_AUDIO_DIRECTORY+filepath
    # print(f"filepath={filepath}")
    print("> Processing audio...")
    s = Song(filepath)
    print("> Audio loaded!")
    print("> Starting Essentia Music Extractor...")
    s.extract()

@app.command(no_args_is_help=True, short_help="Play a beep sound on each downbeat")
def mark_downbeats(
        filepath: Annotated[str, typer.Argument(help="Filepath to song")], 
        output: Annotated[Optional[str], typer.Option('--output', '-o')] = "",
    ):
    filepath = config.BASE_AUDIO_DIRECTORY+filepath
    s = Song(filepath)
    if not output:
        output = f"{s.song_name}--marked-downbeats.wav"
    output = config.BASE_AUDIO_DIRECTORY+output

    marked_audio = utils.onset_mark_downbeats(s)
    utils.save_audio(marked_audio, output)
    print(f"Song marked downbeats saved to: {output}")

@app.command(no_args_is_help=True, short_help="Cut a song between two downbeats", help="Example usage: cut-song /path/to/song.mp3 20 50")
def cut_song(
        filepath: Annotated[str, typer.Argument(help="Filepath to song")], 
        from_downbeat: Annotated[int, typer.Argument(help="Downbeat(bar) to start to cut from")],
        to_downbeat: Annotated[int, typer.Argument(help="Downbeat(bar) to end to cut to")],
        output: Annotated[Optional[str], typer.Option('--output', '-o')] = "",
    ):
    
    assert from_downbeat < to_downbeat
    filepath = config.BASE_AUDIO_DIRECTORY+filepath
    s = Song(filepath)
    dbeats = s.get_downbeats()

    if not output:
        output = f"{s.song_name}--{from_downbeat}-{to_downbeat}.{s.song_format}"
    output = config.BASE_AUDIO_DIRECTORY+output
    
    cut_song = transition.crop_audio_and_dbeats(s, from_downbeat, to_downbeat)
    utils.save_audio(cut_song.audio, output)

    print(f"Song cut between downbeats {from_downbeat}:{to_downbeat}/{len(dbeats)} to: {output}")
    

def main():
    """Console-script entry point for the pycrossfade CLI."""
    app()


if __name__ == "__main__":
    main()



