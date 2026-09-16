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
