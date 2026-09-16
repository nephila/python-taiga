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


MINIMAL_FIELDS: dict[str, list[str]] = {
    "milestone": ["id", "name", "slug", "project", "estimated_start", "estimated_finish", "closed"],
    "userstory": [
        "id",
        "ref",
        "subject",
        "version",
        "milestone",
        "milestone_name",
        "status",
        "status_extra_info.name",
        "status_extra_info.is_closed",
        "is_closed",
        "finish_date",
        "is_blocked",
        "assigned_to_extra_info.full_name_display",
        "epics.ref",
        "assigned_users_extra_info",
    ],
    "issue": [
        "id",
        "ref",
        "subject",
        "version",
        "milestone",
        "milestone_name",
        "status",
        "status_extra_info.name",
        "status_extra_info.is_closed",
        "is_closed",
        "finish_date",
        "is_blocked",
        "assigned_to_extra_info.full_name_display",
        "epics.ref",
    ],
    "epic": ["id", "ref", "subject", "status_extra_info.name", "project"],
}


def _merge_paths(projected: dict[str, Any], source: dict[str, Any], paths: list[str]) -> dict[str, Any]:
    """Copy each named top-level key's full, unprojected value from `source` into `projected`."""
    result = dict(projected)
    for key in paths:
        if key in source:
            result[key] = source[key]
    return result


def apply_payload(
    data: Any,
    entity: str,
    *,
    payload: str = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
) -> Any:
    """Apply the payload/fields/strip_media/expand projection to a jsonable dict/list.

    `payload="full"` with `fields`/`expand` both unset and `strip_media` not explicitly
    `True` is always identity - this is what guarantees the byte-identical-by-default
    compatibility contract. `MINIMAL_FIELDS` only has measured entries for "milestone",
    "userstory", "issue" and "epic"; for any other `entity`, `payload="minimal"` falls
    back to the same projection as `payload="compact"`.
    """
    if payload == "full" and fields is None and expand is None and strip_media in (None, False):
        return data

    if isinstance(data, list):
        return [
            apply_payload(item, entity, payload=payload, fields=fields, strip_media=strip_media, expand=expand)
            for item in data
        ]

    if fields is not None:
        out = select_fields(data, fields)
    elif payload == "minimal":
        minimal_paths = MINIMAL_FIELDS.get(entity)
        out = select_fields(data, minimal_paths) if minimal_paths is not None else collapse_extra_info(data)
    elif payload == "compact":
        out = collapse_extra_info(data)
    else:
        out = data

    strip = strip_media if strip_media is not None else payload in ("compact", "minimal")
    if strip:
        out = strip_avatar_fields(out)

    if expand:
        out = _merge_paths(out, data, expand)

    return out
