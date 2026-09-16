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
