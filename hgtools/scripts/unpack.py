""" Extracts pack.dat """
import os
import shutil
from hglib.pack import HGPack
import click


@click.command()
@click.argument(
    "path_to_pack_dat",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.argument(
    "output_dir",
    type=click.Path(
        file_okay=False, dir_okay=True, readable=True, exists=False, writable=True
    ),
)
@click.option(
    "force",
    "-f",
    is_flag=True,
    default=False,
    help="Don't ask before deleting files inside OUTPUT_DIR",
)
def unpack(path_to_pack_dat: str, output_dir: str, force: bool):
    """
    Pack a pack.dat file.
    Unpacks all files from the pack.dat pack file. Additionally unpacks any of the
    files which are FLK5 files.
    """

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if os.listdir(output_dir) and not force:
        response = input(
            f"Warning! {output_dir} is not empty. This script will delete any files/directories inside. Continue? [y/n]: "
        )
        if response.lower() != "y":
            print("Exiting")
            return

    # Empty out output dir
    for filename in os.listdir(output_dir):
        file_path = os.path.join(output_dir, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

    print("Unpacking pack.dat...")
    with open(path_to_pack_dat, "rb") as pack_f:
        pack = HGPack.from_packed(pack_f)

    pack.to_dir(output_dir)
    print("Unpacking complete.")