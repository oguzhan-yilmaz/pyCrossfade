import typer
from song import Song


app = typer.Typer(
    no_args_is_help=True,
)

# git config --global user.name "Oguzhan Yilmaz"
# git config --global user.email "oguzhan@hepapi.com"


@app.command()
def parse_song(filepath: str):
    print(f"filepath={filepath}")
    s = Song(filepath)
    print(f"downbeats len: {len(s.get_downbeats())}")
    print()

    print(f'Song duration {s.get_duration()}')
    print(f"beats len: {len(s.beats)}")
    
@app.command()
def list_songs(filepath: str):
    print(f"Hello {name}")
    
def main(name: str):
    print(f"Hello {name}")


if __name__ == "__main__":
    app()