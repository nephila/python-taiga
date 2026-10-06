# python-taiga
# Copyright 2015 Nephila
# See LICENSE for details.

from __future__ import annotations

import datetime
from typing import Any

from ..models.base import InstanceResource

_SKIPPED_ATTRS = {"requester"}


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
