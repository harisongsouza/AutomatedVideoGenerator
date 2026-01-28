"""Console script for automated_video_generator."""

import typer
from rich.console import Console
import automated_video_generator.automated_video_generator_method as automated_video_generator_method

app = typer.Typer()
console = Console()

@app.command()
def main():
    automated_video_generator_method.main()

if __name__ == "__main__":
    app()
