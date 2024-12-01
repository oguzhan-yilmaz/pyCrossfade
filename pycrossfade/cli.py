import typer
from song import Song
from utils import print_dict_table


app = typer.Typer(
    no_args_is_help=True,
)

# git config --global user.name "Oguzhan Yilmaz"
# git config --global user.email "oguzhan@hepapi.com"


@app.command()
def parse_song(filepath: str):
    print(f"filepath={filepath}")
    s = Song(filepath)
    s.print_attribute_table()

    
    
@app.command()
def list_songs(filepath: str):
    print(f"Hello {name}")
    
def main(name: str):
    print(f"Hello {name}")


if __name__ == "__main__":
    app()



