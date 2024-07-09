""" Packs pack.dat """

import os
import sys
from hglib.hgscript import HGScriptCollection
import click


@click.command()
@click.argument(
    "input_dir",
    type=click.Path(
        file_okay=False, dir_okay=True, readable=True, exists=False, writable=True
    ),
)
@click.argument(
    "path_to_unpacked",
    type=click.Path(file_okay=False, dir_okay=True, readable=True),
)
def compile_hgscript(input_dir: str, path_to_unpacked: str):
    """
    Build XML HGScript files back into binary HGScriptCollections.
    Given a path to decompiled HGScriptCollections, builds each one back into its
    appropriate binary file in <path_to_pack_dat>.
    """

    print("Compiling hgscript")
    for dir in os.listdir(input_dir):
        """
        if int(dir.split("_")[0]) != 1:
            continue
        if int(dir.split("_")[1].split(".")[0]) < 50:
            continue
        """
        original_path = os.path.join(path_to_unpacked, dir.replace("_", "/"))
        if not os.path.isfile(original_path):
            sys.exit(f"Could not find file {original_path}")
        coll = HGScriptCollection.from_dir(os.path.join(input_dir, dir))
        coll.to_file(original_path)
    print("Done")