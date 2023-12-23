import click
from hgtools.scripts.extract_iso import extract_iso
from hgtools.scripts.unpack import unpack
from hgtools.scripts.pack import pack
from hgtools.scripts.decompile_hgscript import decompile_hgscript
from hgtools.scripts.compile_hgscript import compile_hgscript

@click.group()
def cli():
    pass


cli.add_command(extract_iso)
cli.add_command(unpack)
cli.add_command(pack)
cli.add_command(decompile_hgscript)
cli.add_command(compile_hgscript)

if __name__ == "__main__":
    cli()
