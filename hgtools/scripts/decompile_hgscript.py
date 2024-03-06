""" Extracts pack.dat """

import os
import sys
import shutil
from hglib.hgscript import HGScriptCollection
import click
from hgtools.scripts.hgscript_paths import hgscript_paths


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
def decompile_hgscript(path_to_unpacked: str, output_dir: str, force: bool):
    """
    Dump binary HGScriptCollection files to XML.
    Given a path to an unpacked pack.dat, decompiles all hgscript collections and dumps
    them as XML in <output_dir>
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

    for item in hgscript_paths:
        path = os.path.join(path_to_unpacked, item["path"])
        if not os.path.isfile(path):
            sys.exit(
                f"Expected HGScriptCollection file {path} could not be found. Is {path_to_unpacked} an unpacked pack.dat?"
            )
        orig_hgscript_filesizes[path] = os.stat(path).st_size
        has_object_header = item["has_object_header"]
        coll = HGScriptCollection.from_file(path, has_object_header=has_object_header)
        output_dir_name = item["path"].replace("/", "_").replace("\\", "_")
        output_path = os.path.join(output_dir, output_dir_name)
        os.makedirs(output_path)
        coll.to_dir(output_path)
