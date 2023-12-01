# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Main entry point into capella_diff_tools."""
from __future__ import annotations

import datetime
import logging
import sys
import typing as t

import capellambse
import click
import markupsafe
import yaml
from capellambse.filehandler import git as gitfh
from capellambse.model import common as c

import capella_diff_tools

from . import compare, report, types

logger = logging.getLogger(__name__)

_T = t.TypeVar("_T", bound=c.GenericElement)


@click.command()
@click.version_option(
    version=capella_diff_tools.__version__,
    prog_name="Capella Diff Tools",
    message="%(prog)s %(version)s",
)
@click.argument("model", type=capellambse.cli_helpers.ModelInfoCLI())
@click.argument("old_version")
@click.argument("new_version")
@click.option(
    "-o",
    "--output",
    "output_file",
    type=click.File("w"),
    help="Write the diff report as YAML",
)
@click.option(
    "-r",
    "--report",
    "report_file",
    type=click.File("w"),
    help="Generate a human-readable HTML report",
)
def main(
    model: dict[str, t.Any],
    old_version: str,
    new_version: str,
    output_file: t.IO[str] | None,
    report_file: t.IO[str] | None,
) -> None:
    """Generate the diff summary between two model versions.

    If neither '--output' nor '--report' are specified, the result is
    written in YAML format to stdout.
    """
    logging.basicConfig(level="DEBUG")
    if "revision" in model:
        del model["revision"]
    old_model = capellambse.MelodyModel(**model, revision=old_version)
    new_model = capellambse.MelodyModel(**model, revision=new_version)

    metadata: types.Metadata = {
        "model": model,
        "old_revision": _get_revision_info(old_model, old_version),
        "new_revision": _get_revision_info(new_model, new_version),
    }
    objects = compare.compare_all_objects(old_model, new_model)
    diagrams = compare.compare_all_diagrams(old_model, new_model)

    result: types.ChangeSummaryDocument = {
        "metadata": metadata,
        "diagrams": diagrams,
        "objects": objects,
    }

    if output_file is report_file is None:
        output_file = sys.stdout

    if output_file is not None:
        yaml.dump(result, output_file, Dumper=CustomYAMLDumper)
    if report_file is not None:
        report_file.write(report.generate_html(result))


def _get_revision_info(
    model: capellambse.MelodyModel,
    revision: str,
) -> types.RevisionInfo:
    """Return the revision info of the given model."""
    info = model.info
    fh = model._loader.resources["\x00"]
    assert isinstance(fh, gitfh.GitFileHandler)
    author, date_str, description = fh._git(
        "log",
        "-1",
        "--format=%aN%x00%aI%x00%B",
        info.rev_hash,
        encoding="utf-8",
    ).split("\x00")
    assert info.rev_hash is not None
    return {
        "hash": info.rev_hash,
        "revision": revision,
        "author": author,
        "date": datetime.datetime.fromisoformat(date_str),
        "description": description.rstrip(),
    }


class CustomYAMLDumper(yaml.SafeDumper):
    """A custom YAML dumper that can serialize markupsafe.Markup."""

    def represent_markup(self, data):
        """Represent markupsafe.Markup with the '!html' tag."""
        return self.represent_scalar("!html", str(data))


CustomYAMLDumper.add_representer(
    markupsafe.Markup, CustomYAMLDumper.represent_markup
)


if __name__ == "__main__":
    main()
