""" Extracts the Hungry Ghosts ISO """
import collections
import hashlib
import os
import shutil
import sys

import click
import pycdlib

CORRECT_SHA256 = "8ca1513c8417c0a40b838ff5edf22a2360f43bce1b0458693a95a6efdafd994e"


def iso_is_valid(path_to_iso: str) -> bool:
    """
    Checks if the provided ISO's hash matches the correct one.
    """
    with open(path_to_iso, "rb") as f:
        digest = hashlib.file_digest(f, "sha256")
    return digest.hexdigest() == extract_iso.CORRECT_SHA256


@click.command()
@click.argument(
    "path_to_iso",
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
@click.option("quick", "-q", is_flag=True, default=False, help="Skip ISO hash check")
def extract_iso(path_to_iso: str, output_dir: str, force: bool, quick: bool):
    """
    Extracts PATH_TO_ISO and places contents in OUTPUT_DIR. If OUTPUT_DIR doesn't exist
    it will be created.
    """
    if not quick and not iso_is_valid(path_to_iso):
        sys.exit(
            f"SHA256 hash of {path_to_iso} does not match expected value of {CORRECT_SHA256}. Make sure this is the right .iso!"
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

    # The following section is based off of the 'extract-files.py' script included with
    # pycdlib
    iso = pycdlib.PyCdlib()
    print("Opening %s" % path_to_iso)
    iso.open(path_to_iso)

    pathname = "udf_path"

    root_entry = iso.get_record(**{pathname: "/"})

    dirs = collections.deque([root_entry])
    while dirs:
        dir_record = dirs.popleft()
        ident_to_here = iso.full_path_from_dirrecord(
            dir_record, rockridge=pathname == "rr_path"
        )
        relname = ident_to_here[len("/") :]
        if relname and relname[0] == "/":
            relname = relname[1:]

        if dir_record.is_dir():
            if relname != "":
                os.makedirs(os.path.join(output_dir, relname))
            child_lister = iso.list_children(**{pathname: ident_to_here})

            for child in child_lister:
                if child is None or child.is_dot() or child.is_dotdot():
                    continue
                dirs.append(child)
        else:
            if dir_record.is_symlink():
                fullpath = os.path.join(output_dir, relname)
                local_dir = os.path.dirname(fullpath)
                local_link_name = os.path.basename(fullpath)
                old_dir = os.getcwd()
                os.chdir(local_dir)
                os.symlink(dir_record.rock_ridge.symlink_path(), local_link_name)
                os.chdir(old_dir)
            else:
                iso.get_file_from_iso(
                    os.path.join(output_dir, relname), **{pathname: ident_to_here}
                )
    iso.close()
    print("ISO extraction complete")
