<!--
 ~ Copyright DB Netz AG and contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Capella Diff Tools

[![Lint](https://github.com/DSD-DBS/capella-diff-tools/actions/workflows/lint.yml/badge.svg)](https://github.com/DSD-DBS/capella-diff-tools/actions/workflows/lint.yml)
[![Apache 2.0 License](https://img.shields.io/github/license/dsd-dbs/capella-diff-tools)](LICENSES/Apache-2.0.txt)
[![Code style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

*Tools for comparing different versions of a Capella model*

![Screenshot of the HTML report comparing two versions of the coffee-machine demo model](docs/source/_static/screenshot.png)

# Quick start

Run the `capella-diff-tool` with a Git repo and two versions, being either
commit hashes or branch names:

```sh
capella-diff-tool coffee-machine index-links/base index-links/left
```

```yaml
diagrams:
  sa:
    Missions Capabilities Blank:
      modified:
      - display_name: '[MCB] Capabilities'
        uuid: _J1uyIFucEe2iJbuWznnyfw
    System Architecture Blank:
      modified:
      - display_name: '[SAB] make coffee'
        uuid: _MWuNkFuvEe2iJbuWznnyfw
    System Data Flow Blank:
      modified:
      - display_name: '[SDFB] make coffee'
        uuid: _FOutoFujEe2iJbuWznnyfw
metadata:
  model:
    path: git+https://github.com/DSD-DBS/coffee-machine.git
  new_revision:
    author: martinlehmann
    date: 2023-09-27 14:31:03+02:00
    description: 'fix: Inflation is real, we cannot afford real coffee [skip ci]'
    hash: 908a6b909dcdc071ffc0c424502d8f47d82d9f49
    revision: index-links/left
  old_revision:
    author: martinlehmann
    date: 2023-09-27 14:30:47+02:00
    description: 'refactor: Fragment out SA and OA [skip ci]'
    hash: cb0918af3df822344a80eda3fef6463bcf4c36f3
    revision: index-links/base
objects:
  sa:
    SystemFunction:
      modified:
      - attributes:
          name:
            current: make black water
            previous: make coffee
        display_name: make black water
        uuid: 8b0d19df-7446-4c3a-98e7-4a739c974059
```

The CLI's first argument accepts the name of a [known model], a local folder,
or JSON describing a remote model. Currently it only supports Git, but a
[Python API] is available for more advanced comparisons.

[known model]: https://dsd-dbs.github.io/py-capellambse/start/specifying-models.html#known-models
[Python API]: #api-documentation

The `capella-diff-tool` can also generate a human-friendly report in HTML form.
Use the `-r` / `--report` flag and specify a filename to write the HTML report:

```sh
capella-diff-tool coffee-machine index-links/base index-links/left -r coffee-machine.html
```

# Installation

You can install the latest released version directly from PyPI.

```sh
pip install capella-diff-tools
```

To set up a development environment, clone the project and install it into a
virtual environment.

```sh
git clone https://github.com/DSD-DBS/capella-diff-tools
cd capella-diff-tools
python -m venv .venv

source .venv/bin/activate.sh  # for Linux / Mac
.venv\Scripts\activate  # for Windows

pip install -U pip pre-commit
pip install -e '.[docs,test]'
pre-commit install
```

# API Documentation

The `capella_diff_tools` Python package exposes a Python API, which can be used
to compare arbitrary models programmatically. Documentation for this API is
[available on Github pages](https://dsd-dbs.github.io/capella-diff-tools).

# Contributing

We'd love to see your bug reports and improvement suggestions! Please take a
look at our [guidelines for contributors](CONTRIBUTING.md) for details.

# Licenses

This project is compliant with the
[REUSE Specification Version 3.0](https://git.fsfe.org/reuse/docs/src/commit/d173a27231a36e1a2a3af07421f5e557ae0fec46/spec.md).

Copyright DB Netz AG, licensed under Apache 2.0 (see full text in
[LICENSES/Apache-2.0.txt](LICENSES/Apache-2.0.txt))

Dot-files are licensed under CC0-1.0 (see full text in
[LICENSES/CC0-1.0.txt](LICENSES/CC0-1.0.txt))
