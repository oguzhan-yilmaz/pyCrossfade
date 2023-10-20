import typer
from song import Song

def main(name: str):
    print(f"Hello {name}")


if __name__ == "__main__":
    typer.run(main)
