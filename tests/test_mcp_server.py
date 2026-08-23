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


# --- _resolve_project_id -----------------------------------------------------------------


def test_resolve_project_id_with_int():
    assert server._resolve_project_id(42) == 42


def test_resolve_project_id_with_numeric_string():
    assert server._resolve_project_id("42") == 42


@patch("taiga.mcp_server.server.get_client")
def test_resolve_project_id_with_slug(mock_get_client):
    mock_client = MagicMock()
    mock_client.projects.get_by_slug.return_value = MagicMock(id=7)
    mock_get_client.return_value = mock_client

    assert server._resolve_project_id("my-project") == 7

    mock_client.projects.get_by_slug.assert_called_once_with("my-project")


# --- _paginated ---------------------------------------------------------------------------


def test_paginated_defaults_page_and_page_size():
    assert server._paginated({}) == {"page": 1, "page_size": 100}


def test_paginated_preserves_other_keys():
    assert server._paginated({"project": 1}) == {"project": 1, "page": 1, "page_size": 100}


def test_paginated_does_not_override_explicit_page():
    assert server._paginated({"page": 3}) == {"page": 3, "page_size": 100}


def test_paginated_does_not_override_explicit_page_size():
    assert server._paginated({"page_size": 25}) == {"page": 1, "page_size": 25}


# --- whoami / projects / search ----------------------------------------------------------


@patch("taiga.mcp_server.server.get_client")
def test_whoami(mock_get_client):
    mock_client = MagicMock()
    mock_client.me.return_value = {"id": 1, "username": "tester"}
    mock_get_client.return_value = mock_client

    assert server.whoami() == {"id": 1, "username": "tester"}


@patch("taiga.mcp_server.server.get_client")
def test_list_projects_without_member(mock_get_client):
    mock_client = MagicMock()
    mock_client.projects.list.return_value = [{"id": 1}]
    mock_get_client.return_value = mock_client

    result = server.list_projects()

    mock_client.projects.list.assert_called_once_with(page=1, page_size=100)
    assert result == [{"id": 1}]


@patch("taiga.mcp_server.server.get_client")
def test_list_projects_with_member(mock_get_client):
    mock_client = MagicMock()
    mock_client.projects.list.return_value = [{"id": 1}]
    mock_get_client.return_value = mock_client

    server.list_projects(member=9, filters={"is_backlog_activated": True})

    mock_client.projects.list.assert_called_once_with(is_backlog_activated=True, member=9, page=1, page_size=100)


@patch("taiga.mcp_server.server.get_client")
def test_list_projects_explicit_pagination_not_overridden(mock_get_client):
    mock_client = MagicMock()
    mock_client.projects.list.return_value = [{"id": 1}]
    mock_get_client.return_value = mock_client

    server.list_projects(filters={"page": 3, "page_size": 25, "order_by": "-created_date"})

    mock_client.projects.list.assert_called_once_with(page=3, page_size=25, order_by="-created_date")


@patch("taiga.mcp_server.server.get_client")
def test_get_project_by_id(mock_get_client):
    mock_client = MagicMock()
    mock_client.projects.get.return_value = {"id": 1}
    mock_get_client.return_value = mock_client

    result = server.get_project(1)

    mock_client.projects.get.assert_called_once_with(1)
    assert result == {"id": 1}


@patch("taiga.mcp_server.server.get_client")
def test_get_project_by_slug(mock_get_client):
    mock_client = MagicMock()
    mock_client.projects.get_by_slug.return_value = {"id": 1, "slug": "my-project"}
    mock_get_client.return_value = mock_client

    result = server.get_project("my-project")

    mock_client.projects.get_by_slug.assert_called_once_with("my-project")
    assert result == {"id": 1, "slug": "my-project"}


@patch("taiga.mcp_server.server.get_client")
def test_search(mock_get_client):
    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.count = 2
    mock_result.user_stories = [{"id": 1}]
    mock_result.tasks = []
    mock_result.issues = []
    mock_result.epics = []
    mock_result.wikipages = [{"id": 2}]
    mock_client.search.return_value = mock_result
    mock_get_client.return_value = mock_client

    result = server.search(1, "keyword")

    mock_client.search.assert_called_once_with(1, "keyword")
    assert result == {
        "count": 2,
        "user_stories": [{"id": 1}],
        "tasks": [],
        "issues": [],
        "epics": [],
        "wikipages": [{"id": 2}],
    }


# --- add_comment ---------------------------------------------------------------------------


@patch("taiga.mcp_server.server.get_client")
def test_add_comment_routes_every_entity_type(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    for entity_type, attr in server._ENTITY_ATTR.items():
        resource = getattr(mock_client, attr).get.return_value
        resource.add_comment.return_value = {"comment": "hello"}

        result = server.add_comment(entity_type, 1, "hello")

        getattr(mock_client, attr).get.assert_called_once_with(1)
        resource.add_comment.assert_called_once_with("hello")
        assert result == {"comment": "hello"}


# --- get_history -----------------------------------------------------------------------


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


# --- User stories -----------------------------------------------------------------------


@patch("taiga.mcp_server.server.get_client")
def test_list_user_stories_no_project(mock_get_client):
    mock_client = MagicMock()
    mock_client.user_stories.list.return_value = [{"id": 1}]
    mock_get_client.return_value = mock_client

    result = server.list_user_stories()

    mock_client.user_stories.list.assert_called_once_with(page=1, page_size=100)
    assert result == [{"id": 1}]


@patch("taiga.mcp_server.server.get_client")
def test_list_user_stories_with_project(mock_get_client):
    mock_client = MagicMock()
    mock_client.user_stories.list.return_value = [{"id": 1}]
    mock_get_client.return_value = mock_client

    server.list_user_stories(project=1, filters={"status": 2})

    mock_client.user_stories.list.assert_called_once_with(status=2, project=1, page=1, page_size=100)


@patch("taiga.mcp_server.server.get_client")
def test_get_user_story(mock_get_client):
    mock_client = MagicMock()
    mock_client.user_stories.get.return_value = {"id": 1}
    mock_get_client.return_value = mock_client

    result = server.get_user_story(1)

    mock_client.user_stories.get.assert_called_once_with(1)
    assert result == {"id": 1}


@patch("taiga.mcp_server.server.get_client")
def test_create_user_story(mock_get_client):
    mock_client = MagicMock()
    mock_client.user_stories.create.return_value = {"id": 1, "subject": "New story"}
    mock_get_client.return_value = mock_client

    result = server.create_user_story(1, "New story", fields={"points": {"1": 2}})

    mock_client.user_stories.create.assert_called_once_with(1, "New story", points={"1": 2})
    assert result == {"id": 1, "subject": "New story"}


@patch("taiga.mcp_server.server.get_client")
def test_update_user_story(mock_get_client):
    mock_client = MagicMock()
    mock_resource = MagicMock()
    mock_resource.patch.return_value = {"id": 1, "subject": "Updated"}
    mock_client.user_stories.get.return_value = mock_resource
    mock_get_client.return_value = mock_client

    result = server.update_user_story(1, {"subject": "Updated"})

    mock_client.user_stories.get.assert_called_once_with(1)
    mock_resource.patch.assert_called_once_with(["subject"], subject="Updated")
    assert result == {"id": 1, "subject": "Updated"}


@patch("taiga.mcp_server.server.get_client")
def test_delete_user_story(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    result = server.delete_user_story(1)

    mock_client.user_stories.delete.assert_called_once_with(1)
    assert result == {"status": "deleted", "id": "1"}


# --- Tasks ------------------------------------------------------------------------------


@patch("taiga.mcp_server.server.get_client")
def test_list_tasks_no_filters(mock_get_client):
    mock_client = MagicMock()
    mock_client.tasks.list.return_value = [{"id": 1}]
    mock_get_client.return_value = mock_client

    result = server.list_tasks()

    mock_client.tasks.list.assert_called_once_with(page=1, page_size=100)
    assert result == [{"id": 1}]


@patch("taiga.mcp_server.server.get_client")
def test_list_tasks_with_project_and_user_story(mock_get_client):
    mock_client = MagicMock()
    mock_client.tasks.list.return_value = [{"id": 1}]
    mock_get_client.return_value = mock_client

    server.list_tasks(project=1, user_story=5)

    mock_client.tasks.list.assert_called_once_with(project=1, user_story=5, page=1, page_size=100)


@patch("taiga.mcp_server.server.get_client")
def test_get_task(mock_get_client):
    mock_client = MagicMock()
    mock_client.tasks.get.return_value = {"id": 1}
    mock_get_client.return_value = mock_client

    result = server.get_task(1)

    mock_client.tasks.get.assert_called_once_with(1)
    assert result == {"id": 1}


@patch("taiga.mcp_server.server.get_client")
def test_create_task(mock_get_client):
    mock_client = MagicMock()
    mock_client.tasks.create.return_value = {"id": 1, "subject": "New task"}
    mock_get_client.return_value = mock_client

    result = server.create_task(1, "New task", 3, fields={"user_story": 2})

    mock_client.tasks.create.assert_called_once_with(1, "New task", 3, user_story=2)
    assert result == {"id": 1, "subject": "New task"}


@patch("taiga.mcp_server.server.get_client")
def test_update_task(mock_get_client):
    mock_client = MagicMock()
    mock_resource = MagicMock()
    mock_resource.patch.return_value = {"id": 1, "subject": "Updated"}
    mock_client.tasks.get.return_value = mock_resource
    mock_get_client.return_value = mock_client

    result = server.update_task(1, {"subject": "Updated"})

    mock_client.tasks.get.assert_called_once_with(1)
    mock_resource.patch.assert_called_once_with(["subject"], subject="Updated")
    assert result == {"id": 1, "subject": "Updated"}


@patch("taiga.mcp_server.server.get_client")
def test_delete_task(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    result = server.delete_task(1)

    mock_client.tasks.delete.assert_called_once_with(1)
    assert result == {"status": "deleted", "id": "1"}


# --- Issues -----------------------------------------------------------------------------


@patch("taiga.mcp_server.server.get_client")
def test_list_issues_no_project(mock_get_client):
    mock_client = MagicMock()
    mock_client.issues.list.return_value = [{"id": 1}]
    mock_get_client.return_value = mock_client

    result = server.list_issues()

    mock_client.issues.list.assert_called_once_with(page=1, page_size=100)
    assert result == [{"id": 1}]


@patch("taiga.mcp_server.server.get_client")
def test_list_issues_with_project(mock_get_client):
    mock_client = MagicMock()
    mock_client.issues.list.return_value = [{"id": 1}]
    mock_get_client.return_value = mock_client

    server.list_issues(project=1)

    mock_client.issues.list.assert_called_once_with(project=1, page=1, page_size=100)


@patch("taiga.mcp_server.server.get_client")
def test_list_issues_explicit_pagination_not_overridden(mock_get_client):
    mock_client = MagicMock()
    mock_client.issues.list.return_value = [{"id": 1}]
    mock_get_client.return_value = mock_client

    server.list_issues(project=1, filters={"page": 1, "page_size": 2, "order_by": "-created_date"})

    mock_client.issues.list.assert_called_once_with(project=1, page=1, page_size=2, order_by="-created_date")


@patch("taiga.mcp_server.server.get_client")
def test_get_issue(mock_get_client):
    mock_client = MagicMock()
    mock_client.issues.get.return_value = {"id": 1}
    mock_get_client.return_value = mock_client

    result = server.get_issue(1)

    mock_client.issues.get.assert_called_once_with(1)
    assert result == {"id": 1}


@patch("taiga.mcp_server.server.get_client")
def test_create_issue(mock_get_client):
    mock_client = MagicMock()
    mock_client.issues.create.return_value = {"id": 1, "subject": "New issue"}
    mock_get_client.return_value = mock_client

    result = server.create_issue(1, "New issue", 2, 3, 4, 5, fields={"description": "oops"})

    mock_client.issues.create.assert_called_once_with(1, "New issue", 2, 3, 4, 5, description="oops")
    assert result == {"id": 1, "subject": "New issue"}


@patch("taiga.mcp_server.server.get_client")
def test_update_issue(mock_get_client):
    mock_client = MagicMock()
    mock_resource = MagicMock()
    mock_resource.patch.return_value = {"id": 1, "subject": "Updated"}
    mock_client.issues.get.return_value = mock_resource
    mock_get_client.return_value = mock_client

    result = server.update_issue(1, {"subject": "Updated"})

    mock_client.issues.get.assert_called_once_with(1)
    mock_resource.patch.assert_called_once_with(["subject"], subject="Updated")
    assert result == {"id": 1, "subject": "Updated"}


@patch("taiga.mcp_server.server.get_client")
def test_delete_issue(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    result = server.delete_issue(1)

    mock_client.issues.delete.assert_called_once_with(1)
    assert result == {"status": "deleted", "id": "1"}


# --- Epics ------------------------------------------------------------------------------


@patch("taiga.mcp_server.server.get_client")
def test_list_epics_no_project(mock_get_client):
    mock_client = MagicMock()
    mock_client.epics.list.return_value = [{"id": 1}]
    mock_get_client.return_value = mock_client

    result = server.list_epics()

    mock_client.epics.list.assert_called_once_with(page=1, page_size=100)
    assert result == [{"id": 1}]


@patch("taiga.mcp_server.server.get_client")
def test_list_epics_with_project(mock_get_client):
    mock_client = MagicMock()
    mock_client.epics.list.return_value = [{"id": 1}]
    mock_get_client.return_value = mock_client

    server.list_epics(project=1)

    mock_client.epics.list.assert_called_once_with(project=1, page=1, page_size=100)


@patch("taiga.mcp_server.server.get_client")
def test_get_epic(mock_get_client):
    mock_client = MagicMock()
    mock_client.epics.get.return_value = {"id": 1}
    mock_get_client.return_value = mock_client

    result = server.get_epic(1)

    mock_client.epics.get.assert_called_once_with(1)
    assert result == {"id": 1}


@patch("taiga.mcp_server.server.get_client")
def test_create_epic(mock_get_client):
    mock_client = MagicMock()
    mock_client.epics.create.return_value = {"id": 1, "subject": "New epic"}
    mock_get_client.return_value = mock_client

    result = server.create_epic(1, "New epic")

    mock_client.epics.create.assert_called_once_with(1, "New epic")
    assert result == {"id": 1, "subject": "New epic"}


@patch("taiga.mcp_server.server.get_client")
def test_update_epic(mock_get_client):
    mock_client = MagicMock()
    mock_resource = MagicMock()
    mock_resource.patch.return_value = {"id": 1, "subject": "Updated"}
    mock_client.epics.get.return_value = mock_resource
    mock_get_client.return_value = mock_client

    result = server.update_epic(1, {"subject": "Updated"})

    mock_client.epics.get.assert_called_once_with(1)
    mock_resource.patch.assert_called_once_with(["subject"], subject="Updated")
    assert result == {"id": 1, "subject": "Updated"}


@patch("taiga.mcp_server.server.get_client")
def test_delete_epic(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    result = server.delete_epic(1)

    mock_client.epics.delete.assert_called_once_with(1)
    assert result == {"status": "deleted", "id": "1"}


# --- Milestones ------------------------------------------------------------------------


@patch("taiga.mcp_server.server.get_client")
def test_list_milestones(mock_get_client):
    mock_client = MagicMock()
    mock_client.milestones.list.return_value = [{"id": 1}]
    mock_get_client.return_value = mock_client

    result = server.list_milestones(1, filters={"closed": False})

    mock_client.milestones.list.assert_called_once_with(closed=False, project=1, page=1, page_size=100)
    assert result == [{"id": 1}]


@patch("taiga.mcp_server.server.get_client")
def test_get_milestone(mock_get_client):
    mock_client = MagicMock()
    mock_client.milestones.get.return_value = {"id": 1}
    mock_get_client.return_value = mock_client

    result = server.get_milestone(1)

    mock_client.milestones.get.assert_called_once_with(1)
    assert result == {"id": 1}


@patch("taiga.mcp_server.server.get_client")
def test_create_milestone(mock_get_client):
    mock_client = MagicMock()
    mock_client.milestones.create.return_value = {"id": 1, "name": "Sprint 1"}
    mock_get_client.return_value = mock_client

    result = server.create_milestone(1, "Sprint 1", "2026-01-01", "2026-01-15")

    mock_client.milestones.create.assert_called_once_with(1, "Sprint 1", "2026-01-01", "2026-01-15")
    assert result == {"id": 1, "name": "Sprint 1"}


@patch("taiga.mcp_server.server.get_client")
def test_delete_milestone(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    result = server.delete_milestone(1)

    mock_client.milestones.delete.assert_called_once_with(1)
    assert result == {"status": "deleted", "id": "1"}


# --- Wiki pages ------------------------------------------------------------------------


@patch("taiga.mcp_server.server.get_client")
def test_list_wiki_pages(mock_get_client):
    mock_client = MagicMock()
    mock_client.wikipages.list.return_value = [{"id": 1}]
    mock_get_client.return_value = mock_client

    result = server.list_wiki_pages(1, filters={"slug": "home"})

    mock_client.wikipages.list.assert_called_once_with(slug="home", project=1, page=1, page_size=100)
    assert result == [{"id": 1}]


@patch("taiga.mcp_server.server.get_client")
def test_get_wiki_page(mock_get_client):
    mock_client = MagicMock()
    mock_client.wikipages.get.return_value = {"id": 1}
    mock_get_client.return_value = mock_client

    result = server.get_wiki_page(1)

    mock_client.wikipages.get.assert_called_once_with(1)
    assert result == {"id": 1}


@patch("taiga.mcp_server.server.get_client")
def test_create_wiki_page(mock_get_client):
    mock_client = MagicMock()
    mock_client.wikipages.create.return_value = {"id": 1, "slug": "home"}
    mock_get_client.return_value = mock_client

    result = server.create_wiki_page(1, "home", "Welcome")

    mock_client.wikipages.create.assert_called_once_with(1, "home", "Welcome")
    assert result == {"id": 1, "slug": "home"}


@patch("taiga.mcp_server.server.get_client")
def test_update_wiki_page(mock_get_client):
    mock_client = MagicMock()
    mock_resource = MagicMock()
    mock_resource.patch.return_value = {"id": 1, "content": "Updated"}
    mock_client.wikipages.get.return_value = mock_resource
    mock_get_client.return_value = mock_client

    result = server.update_wiki_page(1, {"content": "Updated"})

    mock_client.wikipages.get.assert_called_once_with(1)
    mock_resource.patch.assert_called_once_with(["content"], content="Updated")
    assert result == {"id": 1, "content": "Updated"}
