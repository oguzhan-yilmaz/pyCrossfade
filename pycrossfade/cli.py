
import typer
from song import Song
import utils
from typing_extensions import Annotated, Optional, List
import numpy as np 
import transition
import config
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
        len_crossfade: Annotated[ Optional[int], typer.Option('--len-crossfade', '-c', help="Crossfade length in bars")  ]=8,
        len_time_stretch: Annotated[ Optional[int], typer.Option('--len-time-stretch', '-t', help="Time-stretch length in bars")  ]=8,
        output: Annotated[ Optional[str], typer.Option('--output', '-o', help="Save the output audio to") ] = "",
        verbose: Annotated[ Optional[bool], typer.Option('--verbose', '-v',help="Print details about the crossfade") ] = False,
        mark_transitions: Annotated[ Optional[bool], typer.Option('--mark-transitions',help="Play a beep sound at time-stretch, crossfade, and slave starts") ] = False,
    ):
    output = config.BASE_AUDIO_DIRECTORY+output
    
    # print(f"filepath={filepath}")
    # print("> Processing master audio...")
    master_filepath = config.BASE_AUDIO_DIRECTORY+master_filepath
    master_song = Song(master_filepath)
    # print("> Processing slave audio...")

    slave_filepath = config.BASE_AUDIO_DIRECTORY+slave_filepath
    slave_song = Song(slave_filepath)
    crossfade = transition.crossfade(master_song, slave_song, len_crossfade=len_crossfade, len_time_stretch=len_time_stretch)

    crossfade
    if not output:
        output = f"crossfade-{master_song.song_name}---{slave_song.song_name}.wav"
        
    audio = crossfade['audio']
    if mark_transitions:
        mark_indices = (crossfade['time_stretch_start_idx'],crossfade['crossfade_start_idx'],crossfade['slave_start_idx'])
        audio = utils.onset_mark_at_indices(audio, mark_indices)
    utils.save_audio(audio, output)
    if verbose:
        crossfade['saved_file'] = output
        crossfade.pop('slave_remaining_song')
        crossfade.pop('time_stretch_audio')
        crossfade.pop('crossfade_part_audio')
        crossfade.pop('audio')
        crossfade.pop('slave_remaining_audio')
        crossfade.pop('master_initial_audio')
        utils.print_dict_as_table(crossfade)
    else:
        print(f"Crossfade saved to {output}")

@app.command(no_args_is_help=True, short_help="Crossfade between min. of 3 songs")
def crossfade_many(
        song_filepaths: Annotated[  List[str], typer.Argument(help="Songs filepaths [Min 3] (seperated by spaces)")],
        len_crossfade: Annotated[ Optional[int], typer.Option('--len-crossfade', '-c',help="Crossfade length in bars")]=8,
        len_time_stretch: Annotated[ Optional[int], typer.Option('--len-time-stretch', '-t',help="Time-stretch length in bars")]=8,
        output: Annotated[ Optional[str], typer.Option('--output', '-o', help="Save the output audio to (song.wav)") ] = "",
        verbose: Annotated[ Optional[bool], typer.Option('--verbose', '-v',help="Print details about the crossfade") ] = False,
        mark_transitions: Annotated[ Optional[bool], typer.Option('--mark-transitions',help="Play a beep sound at time-stretch, crossfade, and slave starts") ] = False,
    ):
    output = config.BASE_AUDIO_DIRECTORY+output

    # print(f"filepath={filepath}")
    song_list = [Song(config.BASE_AUDIO_DIRECTORY+filepath)  for filepath in song_filepaths]
    
    multi_transition = transition.crossfade_multiple(song_list, len_crossfade=len_crossfade, len_time_stretch=len_time_stretch)
    
    output_audio = multi_transition['full_transition']
      
    if mark_transitions:
        output_audio = utils.onset_mark_at_indices(output_audio, multi_transition['transition_indices'])
    
    if not output:
        output = f"crossfadeMany-{'-'.join(s.song_name for s in song_list)}.wav"
    
    utils.save_audio(output_audio, output)

    if verbose:
        print('--verbose option is still in development. Please open an issue.')
        def group_by_three(lst):
            return [lst[i:i+3] for i in range(0, len(lst), 3)]

        transitions_grouped = multi_transition['transition_indices'][:-1]
        last_crossfade_ends = multi_transition['transition_indices'][-1]
        assert len(transitions_grouped)%3==0
        
        transition_g = group_by_three(transitions_grouped)
        utils.print_dict_as_table({
        })
        
    
    
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
    output = config.BASE_AUDIO_DIRECTORY+output
    s = Song(filepath)
    if not output:
        output = f"{s.song_name}--marked-downbeats.wav"
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
    output = config.BASE_AUDIO_DIRECTORY+output
    s = Song(filepath)
    dbeats = s.get_downbeats()

    if not output:
        output = f"{s.song_name}--{from_downbeat}-{to_downbeat}.{s.song_format}"
    
    cut_song = transition.crop_audio_and_dbeats(s, from_downbeat, to_downbeat)
    utils.save_audio(cut_song.audio, output)

    print(f"Song cut between downbeats {from_downbeat}:{to_downbeat}/{len(dbeats)} to: {output}")
    

if __name__ == "__main__":
    app()



