""" Extracts pack.dat """

import os
import shutil
import sys
import tempfile
from glob import glob
from hglib.textures.known_textures import known_textures
from hglib.fonts.known_fonts import known_fonts
from hglib.textures.texture import Texture
from hglib.fonts.font import Font
import click


@click.command()
@click.argument(
    "path_to_unpacked",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
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
def dump_graphics(path_to_unpacked: str, output_dir: str, force: bool):
    """
    Given an directory of unpacked game files, dump out known textures to <output_dir>
    """

    if not shutil.which("magick"):
        sys.exit(
            "ImageMagick not found. This is a requirement for this script. Install it first"
        )

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

    with tempfile.TemporaryDirectory() as tmpdir:
        for file_path in known_textures.keys():
            full_path = os.path.join(path_to_unpacked, file_path)
            slices = known_textures[file_path]["slices"]
            dir_name = known_textures[file_path]["dir_name"]
            # Assume the entire file is the same bpp
            # This may bite me later
            bpp = list(slices.values())[0]["bpp"]
            t = Texture(filename=full_path, slices=slices, bpp=bpp)
            t.dump_slices(os.path.join(tmpdir, dir_name))
        shutil.copytree(os.path.join(tmpdir), output_dir, dirs_exist_ok=True)

    for file_path in known_fonts.keys():
        full_path = os.path.join(path_to_unpacked, file_path)

        title = known_fonts[file_path]["title"]
        width = known_fonts[file_path]["width"]
        height = known_fonts[file_path]["height"]
        interleaved = known_fonts[file_path]["interleaved"]
        font = Font(filename=full_path, title=title, width=width, height=height, interleaved=interleaved)

        font.dump(output_dir)