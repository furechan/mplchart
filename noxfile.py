"""nox configuration

Usage:
    nox            # everyday set: tests + pandas + polars + ruff
    nox -t full    # full pre-publish matrix (Python 3.10-3.14)
    nox -l         # list sessions

Requires nox installed at the system level; uv supplies the venv backend.
"""

import os
import nox

# nox provisions missing interpreters via `uv python install`, which by default
# also symlinks python3.X into ~/.local/bin — keep uv-managed pythons off PATH.
# The interpreters still download into uv's store and are reused from there.
os.environ.setdefault("UV_PYTHON_INSTALL_BIN", "0")

nox.options.default_venv_backend = "uv"
nox.options.envdir = ".venv/nox"
nox.options.sessions = ["tests", "pandas", "polars", "ruff"]

PYTHON_MATRIX = ["3.10", "3.11", "3.12", "3.13", "3.14"]

PYTEST_ENV = {"PYTHONDONTWRITEBYTECODE": "1"}


@nox.session(tags=["full"])
def tests(session):
    """Test suite on the default interpreter with both backends"""
    session.install(".", "pytest", "pandas", "polars")
    session.run("pytest", env=PYTEST_ENV)


@nox.session(python=PYTHON_MATRIX, tags=["full"])
def matrix(session):
    """Test suite across supported Python versions"""
    session.install(".", "pytest", "pandas", "polars")
    session.run("pytest", env=PYTEST_ENV)


# pandas-only install — polars tests skip via importorskip
@nox.session(tags=["full"])
def pandas(session):
    """Test suite with pandas only"""
    session.install(".", "pytest", "pandas")
    session.run("pytest", env=PYTEST_ENV)


# polars-only install — pandas tests skip via importorskip
@nox.session(tags=["full"])
def polars(session):
    """Test suite with polars only"""
    session.install(".", "pytest", "polars")
    session.run("pytest", env=PYTEST_ENV)


@nox.session(tags=["full"])
def ruff(session):
    """Lint with ruff"""
    session.install("ruff")
    session.run("ruff", "check")
