import click
from hgtools.scripts.extract_iso import extract_iso


@click.group()
def cli():
    pass


cli.add_command(extract_iso)

if __name__ == "__main__":
    cli()
