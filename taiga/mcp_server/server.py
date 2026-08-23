# python-taiga
# Copyright 2015 Nephila
# See LICENSE for details.

from __future__ import annotations

from typing import Any, Literal

from fastmcp import FastMCP

from .auth import get_client
from .serialize import to_jsonable

mcp = FastMCP(
    name="taiga",
    instructions=(
        "Tools to read and manage Taiga projects: user stories, tasks, issues, epics, "
        "milestones and wiki pages. Configure credentials via the TAIGA_HOST/TAIGA_TOKEN "
        "or TAIGA_HOST/TAIGA_USERNAME/TAIGA_PASSWORD environment variables. "
        "`get_project` returns the full set of statuses/priorities/severities/points ids "
        "needed to create or update entities in that project."
    ),
)

_ENTITY_ATTR = {
    "user_story": "user_stories",
    "task": "tasks",
    "issue": "issues",
    "epic": "epics",
}


def _resolve_project_id(project: str | int) -> int:
    if isinstance(project, int) or str(project).isdigit():
        return int(project)
    client = get_client()
    return client.projects.get_by_slug(str(project)).id


DEFAULT_PAGE_SIZE = 100


def _paginated(query: dict[str, Any]) -> dict[str, Any]:
    """Default a list query to a single bounded page.

    The underlying client only stops auto-fetching subsequent pages once an explicit
    `page` is given — `page_size` alone does not limit it — so a caller that omits
    `page` would otherwise silently walk and return the *entire* remote collection,
    which for large projects can mean tens of thousands of records in one response.
    Pass `page`/`page_size` inside `filters` to move through further pages.
    """
    query.setdefault("page", 1)
    query.setdefault("page_size", DEFAULT_PAGE_SIZE)
    return query


@mcp.tool
def whoami() -> dict[str, Any]:
    """Return the Taiga user currently authenticated."""
    return to_jsonable(get_client().me())


@mcp.tool
def list_projects(member: int | None = None, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """List projects visible to the authenticated user, optionally filtered by member id.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.
    """
    query = dict(filters or {})
    if member is not None:
        query["member"] = member
    return to_jsonable(get_client().projects.list(**_paginated(query)))


@mcp.tool
def get_project(project: str | int) -> dict[str, Any]:
    """Get full project detail by numeric id or slug, including statuses/priorities/severities/points."""
    client = get_client()
    if isinstance(project, int) or str(project).isdigit():
        return to_jsonable(client.projects.get(int(project)))
    return to_jsonable(client.projects.get_by_slug(str(project)))


@mcp.tool
def search(project: str | int, text: str = "") -> dict[str, Any]:
    """Search user stories, tasks, issues, epics and wiki pages in a project."""
    client = get_client()
    result = client.search(_resolve_project_id(project), text)
    return {
        "count": result.count,
        "user_stories": to_jsonable(result.user_stories),
        "tasks": to_jsonable(result.tasks),
        "issues": to_jsonable(result.issues),
        "epics": to_jsonable(result.epics),
        "wikipages": to_jsonable(result.wikipages),
    }


@mcp.tool
def add_comment(
    entity_type: Literal["user_story", "task", "issue", "epic"], id: int, comment: str
) -> dict[str, Any]:  # noqa: A002
    """Add a comment to a user story, task, issue or epic."""
    client = get_client()
    resource = getattr(client, _ENTITY_ATTR[entity_type]).get(id)
    return to_jsonable(resource.add_comment(comment))


_HISTORY_ENTITY_TYPES = ("user_story", "task", "issue", "epic", "wiki")


@mcp.tool
def get_history(
    entity_type: Literal["user_story", "task", "issue", "epic", "wiki"], id: int  # noqa: A002
) -> list[dict[str, Any]]:
    """Get the full change/comment history of a user story, task, issue, epic or wiki page.

    Each entry has a `comment` field (empty string for pure field-change events, non-empty
    for an actual comment) and `delete_comment_date` (non-null if the comment was deleted).
    """
    client = get_client()
    return to_jsonable(getattr(client.history, entity_type).get(id))


# --- User stories -----------------------------------------------------------------


@mcp.tool
def list_user_stories(project: str | int | None = None, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """List user stories, optionally scoped to a project and/or filtered by extra query params.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.
    """
    query = dict(filters or {})
    if project is not None:
        query["project"] = _resolve_project_id(project)
    return to_jsonable(get_client().user_stories.list(**_paginated(query)))


@mcp.tool
def get_user_story(id: int) -> dict[str, Any]:  # noqa: A002
    """Get a user story by id."""
    return to_jsonable(get_client().user_stories.get(id))


@mcp.tool
def create_user_story(project: str | int, subject: str, fields: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a user story. `fields` may set status, points, milestone, description, tags, etc."""
    pid = _resolve_project_id(project)
    return to_jsonable(get_client().user_stories.create(pid, subject, **(fields or {})))


@mcp.tool
def update_user_story(id: int, fields: dict[str, Any]) -> dict[str, Any]:  # noqa: A002
    """Update a user story. `fields` is a dict of the attributes to change."""
    resource = get_client().user_stories.get(id)
    return to_jsonable(resource.patch(list(fields.keys()), **fields))


@mcp.tool
def delete_user_story(id: int) -> dict[str, str]:  # noqa: A002
    """Delete a user story by id."""
    get_client().user_stories.delete(id)
    return {"status": "deleted", "id": str(id)}


# --- Tasks --------------------------------------------------------------------------


@mcp.tool
def list_tasks(
    project: str | int | None = None, user_story: int | None = None, filters: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """List tasks, optionally scoped to a project and/or a user story.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.
    """
    query = dict(filters or {})
    if project is not None:
        query["project"] = _resolve_project_id(project)
    if user_story is not None:
        query["user_story"] = user_story
    return to_jsonable(get_client().tasks.list(**_paginated(query)))


@mcp.tool
def get_task(id: int) -> dict[str, Any]:  # noqa: A002
    """Get a task by id."""
    return to_jsonable(get_client().tasks.get(id))


@mcp.tool
def create_task(project: str | int, subject: str, status: int, fields: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a task. `status` is the numeric task-status id (see get_project). `fields` may set user_story, etc."""
    pid = _resolve_project_id(project)
    return to_jsonable(get_client().tasks.create(pid, subject, status, **(fields or {})))


@mcp.tool
def update_task(id: int, fields: dict[str, Any]) -> dict[str, Any]:  # noqa: A002
    """Update a task. `fields` is a dict of the attributes to change."""
    resource = get_client().tasks.get(id)
    return to_jsonable(resource.patch(list(fields.keys()), **fields))


@mcp.tool
def delete_task(id: int) -> dict[str, str]:  # noqa: A002
    """Delete a task by id."""
    get_client().tasks.delete(id)
    return {"status": "deleted", "id": str(id)}


# --- Issues ---------------------------------------------------------------------------


@mcp.tool
def list_issues(project: str | int | None = None, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """List issues, optionally scoped to a project.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.
    """
    query = dict(filters or {})
    if project is not None:
        query["project"] = _resolve_project_id(project)
    return to_jsonable(get_client().issues.list(**_paginated(query)))


@mcp.tool
def get_issue(id: int) -> dict[str, Any]:  # noqa: A002
    """Get an issue by id."""
    return to_jsonable(get_client().issues.get(id))


@mcp.tool
def create_issue(
    project: str | int,
    subject: str,
    priority: int,
    status: int,
    issue_type: int,
    severity: int,
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create an issue. `priority`/`status`/`issue_type`/`severity` are numeric ids (see get_project)."""
    pid = _resolve_project_id(project)
    return to_jsonable(
        get_client().issues.create(pid, subject, priority, status, issue_type, severity, **(fields or {}))
    )


@mcp.tool
def update_issue(id: int, fields: dict[str, Any]) -> dict[str, Any]:  # noqa: A002
    """Update an issue. `fields` is a dict of the attributes to change."""
    resource = get_client().issues.get(id)
    return to_jsonable(resource.patch(list(fields.keys()), **fields))


@mcp.tool
def delete_issue(id: int) -> dict[str, str]:  # noqa: A002
    """Delete an issue by id."""
    get_client().issues.delete(id)
    return {"status": "deleted", "id": str(id)}


# --- Epics ------------------------------------------------------------------------------


@mcp.tool
def list_epics(project: str | int | None = None, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """List epics, optionally scoped to a project.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.
    """
    query = dict(filters or {})
    if project is not None:
        query["project"] = _resolve_project_id(project)
    return to_jsonable(get_client().epics.list(**_paginated(query)))


@mcp.tool
def get_epic(id: int) -> dict[str, Any]:  # noqa: A002
    """Get an epic by id."""
    return to_jsonable(get_client().epics.get(id))


@mcp.tool
def create_epic(project: str | int, subject: str, fields: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create an epic."""
    pid = _resolve_project_id(project)
    return to_jsonable(get_client().epics.create(pid, subject, **(fields or {})))


@mcp.tool
def update_epic(id: int, fields: dict[str, Any]) -> dict[str, Any]:  # noqa: A002
    """Update an epic. `fields` is a dict of the attributes to change."""
    resource = get_client().epics.get(id)
    return to_jsonable(resource.patch(list(fields.keys()), **fields))


@mcp.tool
def delete_epic(id: int) -> dict[str, str]:  # noqa: A002
    """Delete an epic by id."""
    get_client().epics.delete(id)
    return {"status": "deleted", "id": str(id)}


# --- Milestones (sprints) -----------------------------------------------------------------


@mcp.tool
def list_milestones(project: str | int, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """List milestones (sprints) of a project.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.
    """
    pid = _resolve_project_id(project)
    query = dict(filters or {})
    query["project"] = pid
    return to_jsonable(get_client().milestones.list(**_paginated(query)))


@mcp.tool
def get_milestone(id: int) -> dict[str, Any]:  # noqa: A002
    """Get a milestone by id."""
    return to_jsonable(get_client().milestones.get(id))


@mcp.tool
def create_milestone(
    project: str | int,
    name: str,
    estimated_start: str,
    estimated_finish: str,
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a milestone. Dates are ISO strings ('YYYY-MM-DD')."""
    pid = _resolve_project_id(project)
    return to_jsonable(get_client().milestones.create(pid, name, estimated_start, estimated_finish, **(fields or {})))


@mcp.tool
def delete_milestone(id: int) -> dict[str, str]:  # noqa: A002
    """Delete a milestone by id."""
    get_client().milestones.delete(id)
    return {"status": "deleted", "id": str(id)}


# --- Wiki pages -----------------------------------------------------------------------------


@mcp.tool
def list_wiki_pages(project: str | int, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """List wiki pages of a project.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.
    """
    pid = _resolve_project_id(project)
    query = dict(filters or {})
    query["project"] = pid
    return to_jsonable(get_client().wikipages.list(**_paginated(query)))


@mcp.tool
def get_wiki_page(id: int) -> dict[str, Any]:  # noqa: A002
    """Get a wiki page by id."""
    return to_jsonable(get_client().wikipages.get(id))


@mcp.tool
def create_wiki_page(
    project: str | int, slug: str, content: str, fields: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Create a wiki page."""
    pid = _resolve_project_id(project)
    return to_jsonable(get_client().wikipages.create(pid, slug, content, **(fields or {})))


@mcp.tool
def update_wiki_page(id: int, fields: dict[str, Any]) -> dict[str, Any]:  # noqa: A002
    """Update a wiki page. `fields` is a dict of the attributes to change."""
    resource = get_client().wikipages.get(id)
    return to_jsonable(resource.patch(list(fields.keys()), **fields))
