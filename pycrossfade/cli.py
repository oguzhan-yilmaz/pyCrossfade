
import typer
from song import Song
from utils import print_dict_as_table
from typing_extensions import Annotated, Optional

app = typer.Typer(
    no_args_is_help=True,
)

# git config --global user.name "Oguzhan Yilmaz"
# git config --global user.email "oguzhan@hepapi.com"


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
def list_songs(filepath: str):
    print(f"Hello {name}")
    
def main(name: str):
    print(f"Hello {name}")


if __name__ == "__main__":
    app()



