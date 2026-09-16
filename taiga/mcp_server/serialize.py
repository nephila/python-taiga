# python-taiga
# Copyright 2015 Nephila
# See LICENSE for details.

from __future__ import annotations

import datetime
from typing import Any

from ..models.base import InstanceResource

_SKIPPED_ATTRS = {"requester"}
_AVATAR_KEYS = frozenset({"photo", "big_photo", "gravatar_id", "logo_small_url"})


def to_jsonable(value: Any) -> Any:
    """Recursively convert python-taiga models into plain JSON-serializable structures."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    if isinstance(value, InstanceResource):
        return {key: to_jsonable(val) for key, val in vars(value).items() if key not in _SKIPPED_ATTRS}
    if isinstance(value, dict):
        return {key: to_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return str(value)


def strip_avatar_fields(data: Any) -> Any:
    """Recursively drop avatar/logo-URL keys from a jsonable dict/list structure.

    Removes `photo`, `big_photo`, `gravatar_id` and `logo_small_url` wherever they occur,
    regardless of which resource type's `*_extra_info` block they came from - these key
    names are never used for anything but a rotating-signature avatar/logo URL.
    """
    if isinstance(data, dict):
        return {key: strip_avatar_fields(val) for key, val in data.items() if key not in _AVATAR_KEYS}
    if isinstance(data, list):
        return [strip_avatar_fields(item) for item in data]
    return data


def select_fields(data: Any, paths: list[str]) -> Any:
    """Project a jsonable dict/list down to only the requested (optionally dotted) paths."""
    if isinstance(data, list):
        return [_select_from_item(item, paths) if isinstance(item, dict) else item for item in data]
    if isinstance(data, dict):
        return _select_from_item(data, paths)
    return data


def _select_from_item(item: dict[str, Any], paths: list[str]) -> dict[str, Any]:
    groups: dict[str, list[str]] = {}
    for path in paths:
        top, _, rest = path.partition(".")
        groups.setdefault(top, []).append(rest)
    result: dict[str, Any] = {}
    for top, rests in groups.items():
        if top not in item:
            continue
        value = item[top]
        if isinstance(value, (dict, list)) and all(rests):
            result[top] = select_fields(value, rests)
        else:
            result[top] = value
    return result


_LABEL_KEYS = ("name", "full_name_display")
_EXTRA_INFO_EXTRA_KEEP = {"status_extra_info": ("is_closed",)}


def collapse_extra_info(data: Any) -> Any:
    """Shrink every `*_extra_info` block to its id plus whichever descriptive label
    field is present.

    Keeps `name` or `full_name_display` (the only two label fields used across
    owner_extra_info, assigned_to_extra_info, project_extra_info and status_extra_info in
    this codebase), and additionally `is_closed` for status_extra_info specifically, so a
    compact caller can still tell whether an item is closed without expanding the block.
    """
    if isinstance(data, dict):
        result: dict[str, Any] = {}
        for key, value in data.items():
            if key.endswith("_extra_info") and isinstance(value, dict):
                keep = ("id", *_LABEL_KEYS, *_EXTRA_INFO_EXTRA_KEEP.get(key, ()))
                result[key] = {k: value[k] for k in keep if k in value}
            else:
                result[key] = collapse_extra_info(value)
        return result
    if isinstance(data, list):
        return [collapse_extra_info(item) for item in data]
    return data
