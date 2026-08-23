from __future__ import annotations

from unittest.mock import MagicMock, patch

from taiga.mcp_server import server


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
