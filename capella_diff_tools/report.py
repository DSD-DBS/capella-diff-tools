# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

__all__ = [
    "generate_html",
]

import copy
import typing as t

import click
import diff_match_patch
import jinja2
import markupsafe
import yaml

from . import types

ENV = jinja2.Environment(
    trim_blocks=True,
    lstrip_blocks=True,
    loader=jinja2.PackageLoader(__name__.rsplit(".", 1)[0], "."),
)


class _CustomLoader(yaml.SafeLoader):
    def construct_html(self, node):
        data = self.construct_scalar(node)
        return markupsafe.Markup(data)


_CustomLoader.add_constructor("!html", _CustomLoader.construct_html)


def _diff_text(previous, current):
    dmp = diff_match_patch.diff_match_patch()
    diff = dmp.diff_main("\n".join(previous), "\n".join(current))
    dmp.diff_cleanupSemantic(diff)
    return dmp.diff_prettyHtml(diff)


def _diff_objects(previous, current):
    return (
        f"<del>{previous['display_name']}</del>"
        f" → <ins>{current['display_name']}</ins>"
    )


def _diff_lists(previous, current):
    out = []
    previous = {item["uuid"]: item for item in previous}
    for item in current:
        if item["uuid"] not in previous:
            out.append(f"<li><ins>{item}</ins></li>")
        elif item["uuid"] in previous:
            if item["display_name"] != previous[item["uuid"]]["display_name"]:
                out.append(
                    f"<li>{_diff_objects(previous[item['uuid']], item)}</li>"
                )
            else:
                out.append(f"<li>{item['display_name']}</li>")
    current = {item["uuid"]: item for item in current}
    for item in previous:
        if item not in current:
            out.append(f"<li><del>{previous[item]['display_name']}</del></li>")
    return "<ul>" + "".join(out) + "</ul>"


def _traverse_and_diff(data):
    """Traverse the data and perform diff on text fields.

    This function recursively traverses the data and performs an HTML
    diff on every "name" and "description" field that has child keys
    "previous" and "current". The result is stored in a new child key
    "diff".
    """
    updates = {}
    for key, value in data.items():
        if (
            isinstance(value, dict)
            and "previous" in value
            and "current" in value
        ):
            prev_type = type(value["previous"])
            curr_type = type(value["current"])
            if prev_type == curr_type == str:
                diff = _diff_text(
                    value["previous"].splitlines(),
                    value["current"].splitlines(),
                )
                updates[key] = {"diff": diff}
            elif prev_type == curr_type == dict:
                diff = _diff_objects(value["previous"], value["current"])
                updates[key] = {"diff": diff}
            elif prev_type == curr_type == list:
                diff = _diff_lists(value["previous"], value["current"])
                updates[key] = {"diff": diff}

        elif isinstance(value, list):
            for item in value:
                _traverse_and_diff(item)
        elif isinstance(value, dict):
            _traverse_and_diff(value)
    for key, value in updates.items():
        data[key].update(value)
    return data


def _compute_diff_stats(data):
    """Compute the diff stats for the data.

    This function collects the diff stats for the data, i.e. how many
    items each were created, modified or deleted. The results are
    aggregated for each category and subcategory.
    """
    stats = {}
    if "created" in data:
        stats["created"] = len(data["created"])
    if "modified" in data:
        stats["modified"] = len(data["modified"])
    if "deleted" in data:
        stats["deleted"] = len(data["deleted"])
    if not stats:
        for value in data.values():
            if isinstance(value, dict):
                child_stats = _compute_diff_stats(value)
                if "created" in child_stats:
                    stats["created"] = (
                        stats.get("created", 0) + child_stats["created"]
                    )
                if "modified" in child_stats:
                    stats["modified"] = (
                        stats.get("modified", 0) + child_stats["modified"]
                    )
                if "deleted" in child_stats:
                    stats["deleted"] = (
                        stats.get("deleted", 0) + child_stats["deleted"]
                    )
    data["stats"] = stats
    return stats


def generate_html(data: types.ChangeSummaryDocument) -> markupsafe.Markup:
    data = copy.deepcopy(data)
    _compute_diff_stats(data)
    template_data = _traverse_and_diff(data)

    template = ENV.get_template("report.html.jinja")
    html = template.render(data=template_data)
    return markupsafe.Markup(html)


@click.command()
@click.argument("filename", type=click.File("r"))
@click.option(
    "-r",
    "--report",
    "report_file",
    type=click.File("w"),
    help="File to write the HTML report to.",
)
def main(filename: t.IO[str], report_file: t.IO[str]) -> None:
    data = yaml.load(filename, Loader=_CustomLoader)
    html = generate_html(data)
    report_file.write(html)


if __name__ == "__main__":
    main()
