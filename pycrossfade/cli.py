
import typer
from song import Song
import utils
from typing_extensions import Annotated, Optional, List
import numpy as np 
import transition
from pprint import pprint

app = typer.Typer(
    no_args_is_help=True,
)

# git config --global user.name "Oguzhan Yilmaz"
# git config --global user.email "oguzhan@hepapi.com"



@app.command()
def crossfade(
        master_filepath: str,
        slave_filepath: str,
        len_crossfade: Annotated[ Optional[int], typer.Option('--len-crossfade', '-c')  ]=8,
        len_time_stretch: Annotated[ Optional[int], typer.Option('--len-time-stretch', '-t')  ]=8,
        output: Annotated[ Optional[str], typer.Option('--output', '-o') ] = "",
        verbose: Annotated[ Optional[bool], typer.Option('--verbose', '-v') ] = False,
        mark_transitions: Annotated[ Optional[bool], typer.Option('--mark-transitions', '-m') ] = False,
    ):
    # print(f"filepath={filepath}")
    print("> Processing master audio...")
    master_song = Song(master_filepath)
    print("> Processing slave audio...")
    slave_song = Song(slave_filepath)
    crossfade = transition.crossfade(master_song, slave_song, len_crossfade=len_crossfade, len_time_stretch=len_time_stretch)
    # s.print_attribute_table()
    # print(master_song)
    # print(slave_song)
    if not output:
        output = f"crossfade-{master_song.song_name}---{slave_song.song_name}.wav"
        
    audio = crossfade['audio']
    if mark_transitions:
        mark_indices = (crossfade['time_stretch_start_idx'],crossfade['crossfade_start_idx'],crossfade['slave_start_idx'])
        audio = utils.onset_mark_at_indices(audio, mark_indices)
    utils.save_audio(audio, output)
    if verbose:
        crossfade['saved_file'] = output
        utils.print_dict_as_table(crossfade)
    else:
        print("Crossfade saved to {output}")

@app.command()
def crossfade_many(
        song_filepaths: List[str],
        len_crossfade: Annotated[ Optional[int], typer.Option('--len-crossfade', '-c')  ]=8,
        len_time_stretch: Annotated[ Optional[int], typer.Option('--len-time-stretch', '-t')  ]=8,
        output: Annotated[ Optional[str], typer.Option('--output', '-o') ] = ""
    ):
    # print(f"filepath={filepath}")
    song_list = [Song(filepath)  for filepath in song_filepaths]
    
    output_audio = transition.crossfade_multiple(song_list, len_crossfade=len_crossfade, len_time_stretch=len_time_stretch)
    
    if not output:
        output = f"crossfadeM-{'-'.join(s.song_name for s in song_list)}.wav"
    utils.save_audio(output_audio, output)
    
@app.command()
def song(filepath: str):
    # print(f"filepath={filepath}")
    print("> Processing audio...")
    s = Song(filepath)
    print("> Audio loaded!")
    s.print_attribute_table()


@app.command()
def extract(
        filepath: str, 
        save_to_file: Annotated[
            Optional[bool], typer.Option('--save', '-s', prompt="Do you want to save the resulting json of Essentia Music Extractor?") 
        ] = False,
    ):
    # print(f"filepath={filepath}")
    print("> Processing audio...")
    s = Song(filepath)
    print("> Audio loaded!")
    print("> Starting Essentia Music Extractor...")
    s.extract(save_to_file)

@app.command()
def mark_downbeats(
        filepath: str, 
        output: Annotated[
            Optional[str], typer.Option('--output', '-o') 
        ] = "",
    ):
    s = Song(filepath)
    if not output:
        output = f"{s.song_name}--marked-downbeats.mp3"
    marked_audio = utils.onset_mark_downbeats(s)
    
    # save_audio(marked_audio, save_file_to, file_format=song.file_format)
    utils.save_audio(marked_audio, output)

    print(f"Song marked downbeats saved to: {output}")

@app.command()
def cut_song(
        filepath: str, 
        from_bar: int,
        to_bar: int,
        output: Annotated[
            Optional[str], typer.Option('--output', '-o') 
        ] = "",
    ):
    
    assert from_bar < to_bar
    
    s = Song(filepath)
    dbeats = s.get_downbeats()

    if not output:
        output = f"{s.song_name}--{from_bar}-{to_bar}.{s.song_format}"
    
    cut = s.audio[dbeats[from_bar]:dbeats[to_bar]]
    utils.save_audio(cut, output)

    print(f"Song cut between downbeats {from_bar}:{to_bar}/{len(dbeats)} to: {output}")
    

if __name__ == "__main__":
    app()



