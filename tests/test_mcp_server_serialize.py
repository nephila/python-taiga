from __future__ import annotations

import datetime
from unittest.mock import MagicMock

from taiga.mcp_server.serialize import (
    apply_payload,
    collapse_extra_info,
    select_fields,
    strip_avatar_fields,
    to_jsonable,
)
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


def test_strip_avatar_fields_removes_known_keys_from_nested_dict():
    data = {
        "id": 1,
        "owner_extra_info": {
            "full_name_display": "Alice",
            "photo": "https://example.com/a.png",
            "big_photo": "https://example.com/a-big.png",
            "gravatar_id": "abc123",
        },
    }

    result = strip_avatar_fields(data)

    assert result == {"id": 1, "owner_extra_info": {"full_name_display": "Alice"}}


def test_strip_avatar_fields_removes_logo_small_url():
    data = {"project_extra_info": {"name": "Demo", "logo_small_url": "https://example.com/logo.png"}}

    result = strip_avatar_fields(data)

    assert result == {"project_extra_info": {"name": "Demo"}}


def test_strip_avatar_fields_recurses_into_list_of_dicts():
    data = [{"photo": "x", "id": 1}, {"photo": "y", "id": 2}]

    result = strip_avatar_fields(data)

    assert result == [{"id": 1}, {"id": 2}]


def test_strip_avatar_fields_no_op_when_no_avatar_keys_present():
    assert strip_avatar_fields({"id": 1, "subject": "hello"}) == {"id": 1, "subject": "hello"}


def test_strip_avatar_fields_passes_through_non_dict_non_list_values():
    assert strip_avatar_fields("hello") == "hello"
    assert strip_avatar_fields(42) == 42
    assert strip_avatar_fields(None) is None


def test_select_fields_keeps_only_requested_top_level_keys():
    data = {"id": 1, "subject": "hello", "status": 2}

    result = select_fields(data, ["id", "subject"])

    assert result == {"id": 1, "subject": "hello"}


def test_select_fields_projects_dotted_path_into_nested_dict():
    data = {
        "ref": 42,
        "status_extra_info": {"id": 3, "name": "In progress", "color": "#000000"},
    }

    result = select_fields(data, ["ref", "status_extra_info.name"])

    assert result == {"ref": 42, "status_extra_info": {"name": "In progress"}}


def test_select_fields_ignores_paths_not_present_in_item():
    data = {"id": 1}

    result = select_fields(data, ["id", "missing", "missing.nested"])

    assert result == {"id": 1}


def test_select_fields_applies_per_item_when_data_is_a_list():
    data = [{"id": 1, "subject": "a"}, {"id": 2, "subject": "b"}]

    result = select_fields(data, ["id"])

    assert result == [{"id": 1}, {"id": 2}]


def test_select_fields_bare_key_wins_over_dotted_path_for_same_top_level_key():
    data = {"status": {"id": 3, "name": "In progress"}}

    result = select_fields(data, ["status", "status.name"])

    assert result == {"status": {"id": 3, "name": "In progress"}}


def test_select_fields_supports_nested_path_deeper_than_two_levels():
    data = {"a": {"b": {"c": 1, "d": 2}}}

    result = select_fields(data, ["a.b.c"])

    assert result == {"a": {"b": {"c": 1}}}


def test_select_fields_projects_into_each_item_of_a_nested_list():
    data = {"id": 1, "epics": [{"ref": 10, "subject": "Epic A"}, {"ref": 11, "subject": "Epic B"}]}

    result = select_fields(data, ["id", "epics.ref"])

    assert result == {"id": 1, "epics": [{"ref": 10}, {"ref": 11}]}


def test_select_fields_nested_list_items_missing_the_path_are_dropped_down_to_empty_dict():
    data = {"epics": [{"ref": 10}, {"subject": "no ref here"}]}

    result = select_fields(data, ["epics.ref"])

    assert result == {"epics": [{"ref": 10}, {}]}


def test_collapse_extra_info_keeps_id_and_name_for_project_like_blocks():
    data = {
        "id": 1,
        "project_extra_info": {"id": 7, "name": "Demo", "slug": "demo", "logo_small_url": "https://x/y.png"},
    }

    result = collapse_extra_info(data)

    assert result == {"id": 1, "project_extra_info": {"id": 7, "name": "Demo"}}


def test_collapse_extra_info_keeps_id_and_full_name_display_for_user_like_blocks():
    data = {
        "owner_extra_info": {
            "id": 3,
            "full_name_display": "Alice",
            "username": "alice",
            "photo": "https://x/a.png",
        }
    }

    result = collapse_extra_info(data)

    assert result == {"owner_extra_info": {"id": 3, "full_name_display": "Alice"}}


def test_collapse_extra_info_keeps_is_closed_for_status_extra_info_only():
    data = {
        "status_extra_info": {"id": 2, "name": "Done", "is_closed": True, "color": "#00ff00"},
        "project_extra_info": {"id": 7, "name": "Demo", "is_closed": True},
    }

    result = collapse_extra_info(data)

    assert result == {
        "status_extra_info": {"id": 2, "name": "Done", "is_closed": True},
        "project_extra_info": {"id": 7, "name": "Demo"},
    }


def test_collapse_extra_info_recurses_into_list_of_dicts():
    data = [
        {"owner_extra_info": {"id": 1, "full_name_display": "Alice", "photo": "x"}},
        {"owner_extra_info": {"id": 2, "full_name_display": "Bob", "photo": "y"}},
    ]

    result = collapse_extra_info(data)

    assert result == [
        {"owner_extra_info": {"id": 1, "full_name_display": "Alice"}},
        {"owner_extra_info": {"id": 2, "full_name_display": "Bob"}},
    ]


def test_collapse_extra_info_leaves_non_extra_info_keys_untouched():
    data = {"id": 1, "subject": "hello", "user_stories": [{"id": 10}]}

    assert collapse_extra_info(data) == data


def test_collapse_extra_info_collapses_invited_by_despite_the_name_mismatch():
    data = {"invited_by": {"id": 5, "username": "yakky", "full_name_display": "Iacopo Spalletti", "is_active": True}}

    result = collapse_extra_info(data)

    assert result == {"invited_by": {"id": 5, "full_name_display": "Iacopo Spalletti"}}


# --- apply_payload ---------------------------------------------------------------------


def test_apply_payload_returns_data_unchanged_by_default():
    data = {"id": 1, "owner_extra_info": {"photo": "x", "full_name_display": "Alice"}}

    assert apply_payload(data, "userstory") == data
    assert apply_payload(data, "userstory", payload="full") == data


def test_apply_payload_full_with_only_strip_media_strips_without_collapsing():
    # Regression test for the source spec's own pseudocode bug: payload="full" combined
    # with an explicit strip_media=True must strip media only, not fall through to
    # compact's collapse_extra_info behavior.
    data = {
        "id": 1,
        "subject": "hello",
        "owner_extra_info": {"id": 9, "full_name_display": "Alice", "photo": "x", "username": "alice"},
    }

    result = apply_payload(data, "userstory", payload="full", strip_media=True)

    assert result == {
        "id": 1,
        "subject": "hello",
        "owner_extra_info": {"id": 9, "full_name_display": "Alice", "username": "alice"},
    }


def test_apply_payload_compact_collapses_extra_info_and_strips_media_by_default():
    data = {
        "id": 1,
        "owner_extra_info": {"id": 9, "full_name_display": "Alice", "photo": "x"},
    }

    result = apply_payload(data, "userstory", payload="compact")

    assert result == {"id": 1, "owner_extra_info": {"id": 9, "full_name_display": "Alice"}}


def test_apply_payload_compact_with_strip_media_false_keeps_top_level_media():
    data = {"id": 1, "photo": "https://x/a.png"}

    result = apply_payload(data, "membership", payload="compact", strip_media=False)

    assert result == {"id": 1, "photo": "https://x/a.png"}


def test_apply_payload_minimal_uses_the_entity_measured_field_set():
    data = {
        "id": 1,
        "ref": 42,
        "subject": "hello",
        "version": 3,
        "milestone": 7,
        "milestone_name": "Sprint 1",
        "status": 2,
        "status_extra_info": {"id": 2, "name": "Done", "is_closed": True},
        "is_closed": True,
        "finish_date": None,
        "is_blocked": False,
        "assigned_to_extra_info": {"id": 5, "full_name_display": "Bob", "photo": "x"},
        "assigned_users": [10, 11],
        "epics": [{"ref": 10, "subject": "Epic A"}],
        "owner_extra_info": {"id": 9, "full_name_display": "Alice", "photo": "y"},
    }

    result = apply_payload(data, "userstory", payload="minimal")

    assert result == {
        "id": 1,
        "ref": 42,
        "subject": "hello",
        "version": 3,
        "milestone": 7,
        "milestone_name": "Sprint 1",
        "status_extra_info": {"name": "Done", "is_closed": True},
        "is_closed": True,
        "finish_date": None,
        "is_blocked": False,
        "assigned_to_extra_info": {"full_name_display": "Bob"},
        "assigned_users": [10, 11],
        "epics": [{"ref": 10}],
    }


def test_apply_payload_minimal_keeps_assigned_users_extra_info_for_userstory():
    data = {
        "id": 1,
        "ref": 42,
        "subject": "hello",
        "version": 3,
        "milestone": 7,
        "milestone_name": "Sprint 1",
        "status": 2,
        "status_extra_info": {"id": 2, "name": "Done", "is_closed": True},
        "is_closed": True,
        "finish_date": None,
        "is_blocked": False,
        "assigned_to_extra_info": {"id": 5, "full_name_display": "Bob", "photo": "x"},
        "assigned_users": [10, 11],
        "epics": [{"ref": 10, "subject": "Epic A"}],
        "owner_extra_info": {"id": 9, "full_name_display": "Alice", "photo": "y"},
        "assigned_users_extra_info": [
            {"id": 10, "full_name_display": "Alice"},
            {"id": 11, "full_name_display": "Bob"},
        ],
    }

    result = apply_payload(data, "userstory", payload="minimal")

    assert result == {
        "id": 1,
        "ref": 42,
        "subject": "hello",
        "version": 3,
        "milestone": 7,
        "milestone_name": "Sprint 1",
        "status_extra_info": {"name": "Done", "is_closed": True},
        "is_closed": True,
        "finish_date": None,
        "is_blocked": False,
        "assigned_to_extra_info": {"full_name_display": "Bob"},
        "assigned_users": [10, 11],
        "epics": [{"ref": 10}],
        "assigned_users_extra_info": [
            {"id": 10, "full_name_display": "Alice"},
            {"id": 11, "full_name_display": "Bob"},
        ],
    }


def test_apply_payload_minimal_falls_back_to_compact_for_entity_without_a_measured_set():
    data = {"id": 1, "owner_extra_info": {"id": 9, "full_name_display": "Alice", "photo": "x"}}

    result = apply_payload(data, "task", payload="minimal")

    assert result == apply_payload(data, "task", payload="compact")
    assert result == {"id": 1, "owner_extra_info": {"id": 9, "full_name_display": "Alice"}}


def test_apply_payload_fields_overrides_payload():
    data = {"id": 1, "subject": "hello", "status": 2}

    result = apply_payload(data, "userstory", payload="minimal", fields=["id", "subject"])

    assert result == {"id": 1, "subject": "hello"}


def test_apply_payload_expand_adds_full_block_back_on_top_of_minimal():
    data = {
        "id": 1,
        "ref": 42,
        "subject": "hello",
        "version": 3,
        "milestone": 7,
        "milestone_name": "Sprint 1",
        "status": 2,
        "status_extra_info": {"id": 2, "name": "Done", "is_closed": True},
        "is_closed": True,
        "finish_date": None,
        "is_blocked": False,
        "assigned_to_extra_info": {"id": 5, "full_name_display": "Bob", "photo": "x"},
        "epics": [],
    }

    result = apply_payload(data, "userstory", payload="minimal", expand=["assigned_to_extra_info"])

    assert result["assigned_to_extra_info"] == {"id": 5, "full_name_display": "Bob", "photo": "x"}


def test_apply_payload_applies_per_item_when_data_is_a_list():
    data = [{"id": 1, "subject": "a", "status": 2}, {"id": 2, "subject": "b", "status": 3}]

    result = apply_payload(data, "userstory", fields=["id", "subject"])

    assert result == [{"id": 1, "subject": "a"}, {"id": 2, "subject": "b"}]
