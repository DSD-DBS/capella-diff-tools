# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""The capella_diff_tools package."""
from importlib import metadata

try:
    __version__ = metadata.version("capella_diff_tools")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+unknown"
del metadata
