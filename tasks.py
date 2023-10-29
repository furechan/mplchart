""" Ibvoke.py tasks file """

import shutil

from invoke import task
from pathlib import Path

PROJECT_NAME = "mplchart"

@task
def tox(ctx, replace: bool = False):
    command = "tox"
    parking = Path("~/Parking").expanduser()

    if parking.exists():
        workdir = parking / PROJECT_NAME / ".tox"
        command += f" --workdir {workdir}"
    else:
        workdir = None

    if workdir and replace:
        shutil.rmtree(workdir)

    ctx.run(command)

