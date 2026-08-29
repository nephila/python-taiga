from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import pytest

server = pytest.importorskip("taiga.mcp_server.server", reason="the mcp extra is not installed")


_HISTORY_ENTRY = {
    "user": {"pk": 1, "name": "tester"},
    "created_at": "2026-08-20T10:00:00+0000",
    "comment": "hello",
    "comment_html": "<p>hello</p>",
    "delete_comment_date": None,
    "type": 1,
}


@patch("taiga.mcp_server.server.get_client")
def test_get_history_returns_jsonable_entries(mock_get_client):
    mock_client = MagicMock()
    mock_client.history.user_story.get.return_value = [_HISTORY_ENTRY]
    mock_get_client.return_value = mock_client

    result = server.get_history("user_story", 42)

    mock_client.history.user_story.get.assert_called_once_with(42)
    assert result == [_HISTORY_ENTRY]


@patch("taiga.mcp_server.server.get_client")
def test_get_history_routes_every_entity_type(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    for entity_type in ("user_story", "task", "issue", "epic", "wiki"):
        getattr(mock_client.history, entity_type).get.return_value = []
        result = server.get_history(entity_type, 1)
        getattr(mock_client.history, entity_type).get.assert_called_once_with(1)
        assert result == []


class TestMcpCustomAttributes(unittest.TestCase):
    @patch("taiga.mcp_server.server._get_project")
    def test_list_custom_attributes(self, mock_get_project):
        mock_get_project.return_value = MagicMock(
            userstory_custom_attributes=[{"id": 406, "name": "Estimation", "type": "number"}]
        )
        self.assertEqual(
            server.list_custom_attributes("nephila", "user_story"),
            [{"id": 406, "name": "Estimation", "type": "number"}],
        )

    @patch("taiga.mcp_server.server._get_project")
    def test_list_custom_attributes_none_defined(self, mock_get_project):
        mock_get_project.return_value = MagicMock(spec=[])
        self.assertEqual(server.list_custom_attributes("nephila", "epic"), [])

    @patch("taiga.mcp_server.server.get_client")
    def test_get_custom_attributes(self, mock_get_client):
        resource = MagicMock()
        resource.get_attributes.return_value = {"attributes_values": {"406": 13}, "version": 2}
        mock_get_client.return_value.user_stories.get.return_value = resource
        self.assertEqual(
            server.get_custom_attributes("user_story", 10893), {"attributes_values": {"406": 13}, "version": 2}
        )
        mock_get_client.return_value.user_stories.get.assert_called_with(10893)

    @patch("taiga.mcp_server.server._get_project")
    @patch("taiga.mcp_server.server.get_client")
    def test_set_custom_attributes_by_id(self, mock_get_client, mock_get_project):
        resource = MagicMock(project=27)
        resource.set_attributes.return_value = {"attributes_values": {"406": 13}}
        mock_get_client.return_value.user_stories.get.return_value = resource
        server.set_custom_attributes("user_story", 10893, {"406": 13})
        resource.set_attributes.assert_called_with({"406": 13})
        # ids need no lookup, so the project is never fetched
        mock_get_project.assert_not_called()

    @patch("taiga.mcp_server.server._get_project")
    @patch("taiga.mcp_server.server.get_client")
    def test_set_custom_attributes_by_name(self, mock_get_client, mock_get_project):
        resource = MagicMock(project=27)
        resource.set_attributes.return_value = {"attributes_values": {"406": 13}}
        mock_get_client.return_value.user_stories.get.return_value = resource
        mock_get_project.return_value = MagicMock(
            userstory_custom_attributes=[{"id": 406, "name": "Estimation"}, {"id": 14, "name": "Code"}]
        )
        server.set_custom_attributes("user_story", 10893, {"Estimation": 13, "28": "2026-09-01"})
        resource.set_attributes.assert_called_with({406: 13, "28": "2026-09-01"})
        mock_get_project.assert_called_with(27)

    @patch("taiga.mcp_server.server._get_project")
    @patch("taiga.mcp_server.server.get_client")
    def test_set_custom_attributes_unknown_name(self, mock_get_client, mock_get_project):
        resource = MagicMock(project=27)
        mock_get_client.return_value.issues.get.return_value = resource
        mock_get_project.return_value = MagicMock(issue_custom_attributes=[{"id": 10, "name": "Code"}])
        with self.assertRaises(ValueError) as raised:
            server.set_custom_attributes("issue", 1, {"Nope": 1})
        self.assertIn("Nope", str(raised.exception))
        resource.set_attributes.assert_not_called()


class TestMcpEpicUserStories(unittest.TestCase):
    @patch("taiga.mcp_server.server.get_client")
    def test_list_epic_user_stories(self, mock_get_client):
        epic = MagicMock()
        epic.list_related_user_stories.return_value = [{"id": 42, "epic": 1020, "user_story": 10893}]
        mock_get_client.return_value.epics.get.return_value = epic
        self.assertEqual(server.list_epic_user_stories(1020), [{"id": 42, "epic": 1020, "user_story": 10893}])
        mock_get_client.return_value.epics.get.assert_called_with(1020)

    @patch("taiga.mcp_server.server.get_client")
    def test_add_user_story_to_epic(self, mock_get_client):
        epic = MagicMock()
        epic.add_user_story.return_value = {"id": 42, "epic": 1020, "user_story": 10893}
        mock_get_client.return_value.epics.get.return_value = epic
        result = server.add_user_story_to_epic(1020, 10893)
        epic.add_user_story.assert_called_with(10893)
        self.assertEqual(result["user_story"], 10893)

    @patch("taiga.mcp_server.server.get_client")
    def test_remove_user_story_from_epic(self, mock_get_client):
        epic = MagicMock()
        mock_get_client.return_value.epics.get.return_value = epic
        result = server.remove_user_story_from_epic(1020, 10893)
        epic.remove_user_story.assert_called_with(10893)
        self.assertEqual(result, {"status": "removed", "epic": "1020", "user_story": "10893"})
