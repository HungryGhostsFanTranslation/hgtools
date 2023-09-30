import click
from hgtools.scripts.extract_iso import extract_iso
from hgtools.scripts.unpack import unpack


@click.group()
def cli():
    pass


cli.add_command(extract_iso)
cli.add_command(unpack)

if __name__ == "__main__":
    cli()
