from __future__ import annotations

import datetime
from unittest.mock import MagicMock

from taiga.mcp_server.serialize import to_jsonable
from taiga.models.base import InstanceResource


def _make_resource(**params):
    """Build a real InstanceResource the way python-taiga parses an API response."""
    return InstanceResource(MagicMock(name="requester"), **params)


def test_to_jsonable_converts_instance_resource_to_dict():
    resource = _make_resource(id=1, subject="hello")

    result = to_jsonable(resource)

    assert result == {"id": 1, "subject": "hello"}


def test_to_jsonable_skips_requester():
    resource = _make_resource(id=1)

    result = to_jsonable(resource)

    assert "requester" not in result


def test_to_jsonable_recurses_into_nested_instance_resource():
    owner = _make_resource(id=7, full_name="Alice")
    resource = _make_resource(id=1, owner=owner)

    result = to_jsonable(resource)

    assert result == {"id": 1, "owner": {"id": 7, "full_name": "Alice"}}


def test_to_jsonable_recurses_into_list_of_instance_resources():
    members = [_make_resource(id=1), _make_resource(id=2)]
    resource = _make_resource(id=99, members=members)

    result = to_jsonable(resource)

    assert result == {"id": 99, "members": [{"id": 1}, {"id": 2}]}


def test_to_jsonable_converts_dates_parsed_by_instance_resource():
    # InstanceResource.__init__ parses created_date/modified_date matching this exact
    # Taiga API format into real datetime objects - use that format here so the
    # attribute is an actual datetime, not a string, when it reaches to_jsonable.
    resource = _make_resource(id=1, created_date="2026-08-20T10:00:00+0000")

    assert isinstance(resource.created_date, datetime.datetime)

    result = to_jsonable(resource)

    assert result == {"id": 1, "created_date": resource.created_date.isoformat()}


def test_to_jsonable_converts_plain_date_and_datetime_values():
    resource = _make_resource(
        id=1,
        due_date=datetime.date(2026, 1, 1),
        finished_at=datetime.datetime(2026, 1, 1, 12, 30, tzinfo=datetime.UTC),
    )

    result = to_jsonable(resource)

    assert result == {
        "id": 1,
        "due_date": "2026-01-01",
        "finished_at": "2026-01-01T12:30:00+00:00",
    }
