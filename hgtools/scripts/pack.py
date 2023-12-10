""" Packs pack.dat """
import os
from hglib.pack import HGPack
import click

@click.command()
@click.argument(
    "input_dir",
    type=click.Path(
        file_okay=False, dir_okay=True, readable=True, exists=False, writable=True
    ),
)
@click.argument(
    "path_to_pack_dat",
    type=click.Path(file_okay=True, dir_okay=False, readable=True),
)
@click.option(
    "force",
    "-f",
    is_flag=True,
    default=False,
    help="Don't ask before overwriting pack.dat",
)
def pack(input_dir: str, path_to_pack_dat: str, force: bool):
    """
    Given an input dir, repacks all FLK5 files and then packs everything into a 
    pack.dat file.
    """
    if os.path.isfile(path_to_pack_dat) and not force:
        response = input(
            f"Warning! {path_to_pack_dat} already exists. This script will overwrite the file. Continue? [y/n]: "
        )
        if response.lower() != "y":
            print("Exiting")
            return

    pack = HGPack.from_dir(input)

    pack.to_packed(path_to_pack_dat)
    