# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Types for annotating functions in the diff tool."""
from __future__ import annotations

import datetime
import typing as t

import typing_extensions as te


class ChangeSummaryDocument(te.TypedDict):
    metadata: Metadata
    diagrams: DiagramChanges
    objects: ObjectChanges


class Metadata(te.TypedDict):
    model: dict[str, t.Any]
    """The 'modelinfo' used to load the models, sans the revision key."""
    new_revision: RevisionInfo
    old_revision: RevisionInfo


class RevisionInfo(te.TypedDict, total=False):
    hash: te.Required[str]
    """The revision hash."""
    revision: str
    """The original revision passed to the diff tool."""
    author: str
    """The author of the revision, in "Name <email@domain>" format."""
    date: datetime.datetime
    """The time and date of the revision."""
    description: str
    """The description of the revision, i.e. the commit message."""


class DiagramChanges(te.TypedDict, total=False):
    oa: DiagramLayer
    """Changes on diagrams from the OperationalAnalysis layer."""
    sa: DiagramLayer
    """Changes on diagrams from the SystemAnalysis layer."""
    la: DiagramLayer
    """Changes on diagrams from the LogicalAnalysis layer."""
    pa: DiagramLayer
    """Changes on diagrams from the PhysicalAnalysis layer."""
    epbs: DiagramLayer
    """Changes on diagrams from the EPBS layer."""


DiagramLayer: te.TypeAlias = "dict[str, DiagramChange]"


class DiagramChange(te.TypedDict, total=False):
    created: list[FullDiagram]
    """Diagrams that were created."""
    deleted: list[FullDiagram]
    """Diagrams that were deleted."""
    modified: list[ChangedDiagram]
    """Diagrams that were changed."""


class BaseObject(te.TypedDict):
    uuid: str
    display_name: str
    """Name for displaying in the frontend.

    This is usually the ``name`` attribute of the "current" version of
    the object.
    """


class FullDiagram(BaseObject, te.TypedDict):
    """A diagram that was created or deleted."""


class ChangedDiagram(BaseObject, te.TypedDict):
    layout_changes: t.Literal[True]
    """Whether the layout of the diagram changed.

    This will always be true if there were any semantic changes to the
    diagram.
    """
    # FIXME layout_changes cannot be False
    #       If there are semantic changes, the layout will change, too.
    #       If there are no layout changes, there cannot be any semantic
    #       changes.
    #       Therefore, if there are no layout changes, there are no
    #       changes at all, and the diagram will not be listed as
    #       changed.
    introduced: te.NotRequired[list[BaseObject]]
    """Objects that were introduced to the diagram."""
    removed: te.NotRequired[list[BaseObject]]
    """Objects that were removed from the diagram."""
    changed: te.NotRequired[list[BaseObject]]
    """Objects that were changed on the diagram.

    This does not consider layout changes. See :attr:`layout_changes`.
    """


class ObjectChanges(te.TypedDict, total=False):
    oa: ObjectLayer
    """Changes to objects from the OperationalAnalysis layer."""
    sa: ObjectLayer
    """Changes to objects from the SystemAnalysis layer."""
    la: ObjectLayer
    """Changes to objects from the LogicalAnalysis layer."""
    pa: ObjectLayer
    """Changes to objects from the PhysicalAnalysis layer."""
    epbs: ObjectLayer
    """Changes to objects from the EPBS layer."""


ObjectLayer: te.TypeAlias = "dict[str, ObjectChange]"


class ObjectChange(te.TypedDict, total=False):
    created: list[FullObject]
    """Contains objects that were created."""
    deleted: list[FullObject]
    """Contains objects that were deleted."""
    modified: list[ChangedObject]


class FullObject(BaseObject, te.TypedDict):
    attributes: dict[str, t.Any]
    """All attributes that the object has (or had)."""


class ChangedObject(BaseObject, te.TypedDict):
    attributes: dict[str, ChangedAttribute]
    """The attributes that were changed."""


class ChangedAttribute(te.TypedDict):
    previous: t.Any
    """The old value of the attribute."""
    current: t.Any
    """The new value of the attribute."""
