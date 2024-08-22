# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Functions for comparing different types of objects in a Capella model."""
from __future__ import annotations

__all__ = [
    "compare_all_diagrams",
    "compare_all_objects",
]

import enum
import itertools
import logging
import typing as t

import capellambse
import capellambse.model as m
import capellambse.model.common as c

from . import types

logger = logging.getLogger(__name__)

_T = t.TypeVar("_T", bound=c.GenericElement)


def compare_all_diagrams(
    old: capellambse.MelodyModel,
    new: capellambse.MelodyModel,
) -> types.DiagramChanges:
    result: dict[str, types.DiagramLayer] = {}
    for layer in ("oa", "sa", "la", "pa"):  # , "epbs"
        diagrams = _compare_diagrams_on_layer(old, new, layer)
        if diagrams:
            result[layer] = diagrams
    return t.cast(types.DiagramChanges, result)


def _compare_diagrams_on_layer(
    old: capellambse.MelodyModel,
    new: capellambse.MelodyModel,
    layer: str,
) -> types.DiagramLayer:
    logger.debug("Collecting diagrams on layer %s", layer)
    changes: types.DiagramLayer = {}

    old_diags = getattr(old, layer).diagrams
    new_diags = getattr(new, layer).diagrams

    old_uuids = {i.uuid for i in old_diags}
    new_uuids = {i.uuid for i in new_diags}

    for i in sorted(new_uuids - old_uuids):
        dg = new_diags.by_uuid(i)
        typechanges = changes.setdefault(dg.type.value, {})
        typechanges.setdefault("created", []).append(_diag2dict(dg))

    for i in sorted(old_uuids - new_uuids):
        dg = old_diags.by_uuid(i)
        typechanges = changes.setdefault(dg.type.value, {})
        typechanges.setdefault("deleted", []).append(_diag2dict(dg))

    for i in sorted(old_uuids & new_uuids):
        old_dg = old_diags.by_uuid(i)
        dg = new_diags.by_uuid(i)
        logger.debug("Comparing diagram %s with (new) name %s", i, dg.name)
        if diff := _diag2diff(old_dg, dg):
            typechanges = changes.setdefault(dg.type.value, {})
            typechanges.setdefault("modified", []).append(diff)
    return changes


def _diag2dict(
    obj: m.diagram.Diagram | c.GenericElement,
) -> types.FullDiagram:
    """Serialize a diagram element into a dict.

    This function is used for diagrams that were either created or
    deleted, in which case only the names are serialized.
    """
    return {"uuid": obj.uuid, "display_name": _get_name(obj)}


def _diag2diff(
    old: m.diagram.Diagram, new: m.diagram.Diagram
) -> types.ChangedDiagram | None:
    """Serialize the differences between the old and new diagram.

    This function is used for diagrams that were modified. Newly
    introduced elements and removed elements are serialized.

    The new (current) *display-name* is always serialized. If it didn't
    change, it will not have the "previous" key.

    The *layout_changes* flag indicates that the diagram has changed
    positions, sizes or bendpoints for exchanges.
    """
    changes: t.Any = {
        "uuid": new.uuid,
        "display_name": _get_name(new),
    }

    old_nodes = old.nodes
    new_nodes = new.nodes
    old_uuids = {i.uuid for i in old_nodes}
    new_uuids = {i.uuid for i in new_nodes}

    if created_uuids := sorted(new_uuids - old_uuids):
        changes["created"] = [
            _diag2dict(new_nodes._model.by_uuid(i)) for i in created_uuids
        ]
    if deleted_uuids := sorted(old_uuids - new_uuids):
        changes["deleted"] = [
            _diag2dict(old_nodes._model.by_uuid(i)) for i in deleted_uuids
        ]

    return changes


def compare_all_objects(
    old: capellambse.MelodyModel,
    new: capellambse.MelodyModel,
) -> types.ObjectChanges:
    """Compare all objects in the given models."""
    old_objects = _group_all_objects(old)
    new_objects = _group_all_objects(new)

    result: t.Any = {}
    for layer in ("oa", "sa", "la", "pa", "epbs"):
        new_types = set(new_objects.get(layer, []))
        old_types = set(old_objects.get(layer, []))

        for obj_type in new_types & old_types:
            old_layerobjs = old_objects[layer][obj_type]
            new_layerobjs = new_objects[layer][obj_type]
            logging.debug(
                "Comparing objects of type %s (%d -> %d)",
                obj_type,
                len(old_layerobjs),
                len(new_layerobjs),
            )
            changes = _compare_object_type(old_layerobjs, new_layerobjs)
            if changes:
                result.setdefault(layer, {})[obj_type] = changes
    return result


def _group_all_objects(
    model: capellambse.MelodyModel,
) -> dict[str, dict[str, c.ElementList[c.GenericElement]]]:
    """Return a dict of all objects, grouped by layer."""
    result: dict[str, dict[str, c.ElementList[c.GenericElement]]]
    result = {"oa": {}, "sa": {}, "la": {}, "pa": {}}
    for layer, objs in result.items():
        ungrouped = sorted(
            model.search(below=getattr(model, layer)),
            key=lambda i: type(i).__name__,
        )
        for objtype, group in itertools.groupby(ungrouped, key=type):
            objs[objtype.__name__] = c.ElementList(
                model, [i._element for i in group], objtype
            )
    return result


def _compare_object_type(
    old: c.ElementList[_T],
    new: c.ElementList[_T],
) -> types.ObjectChange:
    changes: types.ObjectChange = {}

    old_uuids = {i.uuid for i in old}
    new_uuids = {i.uuid for i in new}

    if created_uuids := new_uuids - old_uuids:
        changes["created"] = [
            _obj2dict(new._model.by_uuid(i)) for i in sorted(created_uuids)
        ]
    if deleted_uuids := old_uuids - new_uuids:
        changes["deleted"] = [
            _obj2dict(old._model.by_uuid(i)) for i in sorted(deleted_uuids)
        ]

    for i in sorted(old_uuids & new_uuids):
        if diff := _obj2diff(old._model.by_uuid(i), new._model.by_uuid(i)):
            changes.setdefault("modified", []).append(diff)
    return changes


def _obj2dict(obj: c.GenericElement) -> types.FullObject:
    """Serialize a model object into a dict.

    This function is used for objects that were either created or
    deleted, in which case all available attributes are serialized.
    """
    attributes: dict[str, t.Any] = {}
    for attr in dir(type(obj)):
        acc = getattr(type(obj), attr, None)
        if not isinstance(acc, c.AttributeProperty) and attr not in [
            "parent",
            "source",
            "target",
            "start",
            "finish",
        ]:
            continue

        val = getattr(obj, attr)
        if val is None:
            continue
        attributes[attr] = _serialize_obj(val)

    if hasattr(obj, "source") and hasattr(obj, "target"):
        attributes["source"] = _serialize_obj(obj.source)
        attributes["target"] = _serialize_obj(obj.target)
    elif hasattr(obj, "start") and hasattr(obj, "finish"):
        attributes["start"] = _serialize_obj(obj.start)
        attributes["finish"] = _serialize_obj(obj.finish)

    return {
        "uuid": obj.uuid,
        "display_name": _get_name(obj),
        "attributes": attributes,
    }


def _obj2diff(
    old: c.GenericElement, new: c.GenericElement
) -> types.ChangedObject | None:
    """Serialize the differences between the old and new object.

    This function is used for objects that were modified. Only the
    attributes that were changed are serialized.

    The new (current) *name* is always serialized. If it didn't change,
    it will not have the "previous" key.
    """
    attributes: dict[str, types.ChangedAttribute] = {}
    for attr in dir(type(old)):
        if (
            not isinstance(
                getattr(type(old), attr, None),
                (
                    c.AttributeProperty,
                    c.AttrProxyAccessor,
                    c.LinkAccessor,
                ),  # c.RoleTagAccessor, c.DirectProxyAccessor
            )
            and attr != "parent"
        ):
            continue

        try:
            old_val = getattr(old, attr, None)
        except TypeError as err:
            if isinstance(err.args[0], str) and err.args[0].startswith(
                f"Mandatory XML attribute {attr!r} not found on "
            ):
                logger.warning(
                    "Mandatory attribute %r not found on old version of %s %r",
                    attr,
                    type(old).__name__,
                    old.uuid,
                )
                old_val = None
            else:
                raise
        try:
            new_val = getattr(new, attr, None)
        except TypeError as err:
            if isinstance(err.args[0], str) and err.args[0].startswith(
                f"Mandatory XML attribute {attr!r} not found on "
            ):
                logger.warning(
                    "Mandatory attribute %r not found on new version of %s %r",
                    attr,
                    type(new).__name__,
                    new.uuid,
                )
                new_val = None
            else:
                raise

        if isinstance(old_val, c.GenericElement) and isinstance(
            new_val, c.GenericElement
        ):
            if old_val.uuid != new_val.uuid:
                attributes[attr] = {
                    "previous": _serialize_obj(old_val),
                    "current": _serialize_obj(new_val),
                }
        elif isinstance(old_val, c.ElementList) and isinstance(
            new_val, c.ElementList
        ):
            if [i.uuid for i in old_val] != [i.uuid for i in new_val]:
                attributes[attr] = {
                    "previous": _serialize_obj(old_val),
                    "current": _serialize_obj(new_val),
                }
        elif old_val != new_val:
            attributes[attr] = {
                "previous": _serialize_obj(old_val),
                "current": _serialize_obj(new_val),
            }

    if not attributes:
        return None
    return {
        "uuid": old.uuid,
        "display_name": _get_name(new),
        "attributes": attributes,
    }


def _serialize_obj(obj: t.Any) -> t.Any:
    if isinstance(obj, c.GenericElement):
        return {"uuid": obj.uuid, "display_name": _get_name(obj)}
    elif isinstance(obj, c.ElementList):
        return [{"uuid": i.uuid, "display_name": _get_name(i)} for i in obj]
    elif isinstance(obj, (enum.Enum, enum.Flag)):
        return obj.name
    return obj


def _get_name(obj: m.diagram.Diagram | c.ModelObject) -> str:
    """Return the object's name.

    If the object doesn't own a name, its type is returned instead.
    """
    return getattr(obj, "name", None) or f"[{type(obj).__name__}]"


def compare_models(
    old: capellambse.MelodyModel,
    new: capellambse.MelodyModel,
):
    """Compare all elements in the given models."""
    changes = {}
    for layer in (
        "oa",
        "sa",
        "la",
        "pa",
    ):
        layer_old = getattr(old, layer)
        layer_new = getattr(new, layer)
        changes[layer] = compare_objects(layer_old, layer_new, old)
    return changes


def compare_objects(
    old_object: capellambse.ModelObject | None,
    new_object: capellambse.ModelObject,
    old_model: capellambse.MelodyModel,
):
    if not (old_object is None or type(old_object) is type(new_object)):
        print(f"{type(old_object).__name__} != {type(new_object).__name__}")
        breakpoint()
    attributes: dict[str, types.ChangedAttribute] = {}
    children = {}
    for attr in dir(type(new_object)):
        acc = getattr(type(new_object), attr, None)
        if isinstance(acc, c.AttributeProperty) and attr == "uuid":
            old_value = getattr(old_object, attr, None)
            new_value = getattr(new_object, attr, None)
            if old_value != new_value:
                attributes[attr] = {
                    "previous": _serialize_obj(old_value),
                    "current": _serialize_obj(new_value),
                }
        elif isinstance(
            acc, c.AttrProxyAccessor | c.LinkAccessor | c.ParentAccessor
        ):
            old_value = getattr(old_object, attr, None)
            new_value = getattr(new_object, attr, None)
            if isinstance(
                old_value, c.GenericElement | type(None)
            ) and isinstance(new_value, c.GenericElement | type(None)):
                if old_value is new_value is None:
                    pass
                elif old_value is None:
                    attributes[attr] = {
                        "previous": None,
                        "current": _serialize_obj(new_value),
                    }
                elif new_value is None:
                    attributes[attr] = {
                        "previous": _serialize_obj(old_value),
                        "current": None,
                    }
                elif old_value.uuid != new_value.uuid:
                    attributes[attr] = {
                        "previous": _serialize_obj(old_value),
                        "current": _serialize_obj(new_value),
                    }
            elif isinstance(
                old_value, c.ElementList | type(None)
            ) and isinstance(new_value, c.ElementList):
                old_value = old_value or []
                if [i.uuid for i in old_value] != [i.uuid for i in new_value]:
                    attributes[attr] = {
                        "previous": _serialize_obj(old_value),
                        "current": _serialize_obj(new_value),
                    }
            else:
                raise RuntimeError(
                    f"Type mismatched between new value and old value:"
                    f" {type(old_value)} != {type(new_value)}"
                )
        elif isinstance(acc, c.RoleTagAccessor | c.DirectProxyAccessor):
            old_value = getattr(old_object, attr, None)
            new_value = getattr(new_object, attr, None)
            if isinstance(
                old_value, c.GenericElement | type(None)
            ) and isinstance(new_value, c.GenericElement | type(None)):
                if old_value is new_value is None:
                    pass
                elif old_value is None:
                    assert new_value is not None
                    children[new_value.uuid] = compare_objects(
                        None, new_value, old_model
                    )
                elif new_value is None:
                    children[old_value.uuid] = {
                        "display_name": _get_name(old_value),
                        "change": "deleted",
                    }
                elif old_value.uuid == new_value.uuid:
                    result = compare_objects(old_value, new_value, old_model)
                    if result:
                        children[new_value.uuid] = result
                else:
                    children[old_value.uuid] = {
                        "display_name": _get_name(old_value),
                        "change": "deleted",
                    }
                    children[new_value.uuid] = compare_objects(
                        None, new_value, old_model
                    )
            elif isinstance(
                old_value, c.ElementList | type(None)
            ) and isinstance(new_value, c.ElementList):
                old_value = old_value or []
                for item in new_value:
                    try:
                        old_item = old_model.by_uuid(item.uuid)
                    except KeyError:
                        old_item = None
                    if old_item is None:
                        children[item.uuid] = compare_objects(
                            None, item, old_model
                        )
                    else:
                        result = compare_objects(old_item, item, old_model)
                        if result:
                            children[item.uuid] = result

                for item in old_value:
                    try:
                        new_object._model.by_uuid(item.uuid)
                    except KeyError:
                        children[item.uuid] = {
                            "display_name": _get_name(item),
                            "change": "deleted",
                        }

    if attributes or children or old_object is None:
        return {
            "display_name": _get_name(new_object),
            "change": "created" if old_object is None else "modified",
            "attributes": attributes,
            "children": children,
        }
    return None
