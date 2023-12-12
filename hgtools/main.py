import click
from hgtools.scripts.extract_iso import extract_iso
from hgtools.scripts.unpack import unpack
from hgtools.scripts.pack import pack


@click.group()
def cli():
    pass


cli.add_command(extract_iso)
cli.add_command(unpack)
cli.add_command(pack)

if __name__ == "__main__":
    cli()
