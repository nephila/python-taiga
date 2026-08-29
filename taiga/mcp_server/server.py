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
        "needed to create or update entities in that project, and `list_custom_attributes` "
        "the ids of its custom fields."
    ),
)

_ENTITY_ATTR = {
    "user_story": "user_stories",
    "task": "tasks",
    "issue": "issues",
    "epic": "epics",
}

_CUSTOM_ATTRIBUTES_ATTR = {
    "user_story": "userstory_custom_attributes",
    "task": "task_custom_attributes",
    "issue": "issue_custom_attributes",
    "epic": "epic_custom_attributes",
}


def _get_project(project: str | int):
    client = get_client()
    if isinstance(project, int) or str(project).isdigit():
        return client.projects.get(int(project))
    return client.projects.get_by_slug(str(project))


def _resolve_project_id(project: str | int) -> int:
    if isinstance(project, int) or str(project).isdigit():
        return int(project)
    client = get_client()
    return client.projects.get_by_slug(str(project)).id


def _custom_attributes(project: str | int, entity_type: str) -> list[dict[str, Any]]:
    return getattr(_get_project(project), _CUSTOM_ATTRIBUTES_ATTR[entity_type], None) or []


def _resolve_custom_attribute_ids(project: str | int, entity_type: str, values: dict[str, Any]) -> dict[str, Any]:
    if all(str(key).isdigit() for key in values):
        return values
    by_name = {attribute["name"]: attribute["id"] for attribute in _custom_attributes(project, entity_type)}
    resolved: dict[str, Any] = {}
    for key, value in values.items():
        if str(key).isdigit():
            resolved[key] = value
        elif key in by_name:
            resolved[by_name[key]] = value
        else:
            raise ValueError(f"Unknown {entity_type} custom field {key!r}. Known fields: {sorted(by_name)}")
    return resolved


@mcp.tool
def whoami() -> dict[str, Any]:
    """Return the Taiga user currently authenticated."""
    return to_jsonable(get_client().me())


@mcp.tool
def list_projects(member: int | None = None, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """List projects visible to the authenticated user, optionally filtered by member id."""
    query = dict(filters or {})
    if member is not None:
        query["member"] = member
    return to_jsonable(get_client().projects.list(**query))


@mcp.tool
def get_project(project: str | int) -> dict[str, Any]:
    """Get full project detail by numeric id or slug, including statuses/priorities/severities/points."""
    return to_jsonable(_get_project(project))


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


# --- Custom fields ----------------------------------------------------------------


@mcp.tool
def list_custom_attributes(
    project: str | int, entity_type: Literal["user_story", "task", "issue", "epic"]
) -> list[dict[str, Any]]:
    """List the custom fields a project defines for user stories, tasks, issues or epics, with their ids."""
    return to_jsonable(_custom_attributes(project, entity_type))


@mcp.tool
def get_custom_attributes(
    entity_type: Literal["user_story", "task", "issue", "epic"], id: int
) -> dict[str, Any]:  # noqa: A002
    """Get the custom field values of a user story, task, issue or epic, keyed by custom field id."""
    resource = getattr(get_client(), _ENTITY_ATTR[entity_type]).get(id)
    return to_jsonable(resource.get_attributes())


@mcp.tool
def set_custom_attributes(
    entity_type: Literal["user_story", "task", "issue", "epic"], id: int, values: dict[str, Any]
) -> dict[str, Any]:  # noqa: A002
    """
    Set custom field values on a user story, task, issue or epic.

    `values` keys are either custom field ids or their names (see `list_custom_attributes`). Only the
    given fields are changed, any other custom field keeps its current value.
    """
    resource = getattr(get_client(), _ENTITY_ATTR[entity_type]).get(id)
    values = _resolve_custom_attribute_ids(resource.project, entity_type, values)
    return to_jsonable(resource.set_attributes(values))


# --- User stories -----------------------------------------------------------------


@mcp.tool
def list_user_stories(project: str | int | None = None, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """List user stories, optionally scoped to a project and/or filtered by extra query params."""
    query = dict(filters or {})
    if project is not None:
        query["project"] = _resolve_project_id(project)
    return to_jsonable(get_client().user_stories.list(**query))


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
    """List tasks, optionally scoped to a project and/or a user story."""
    query = dict(filters or {})
    if project is not None:
        query["project"] = _resolve_project_id(project)
    if user_story is not None:
        query["user_story"] = user_story
    return to_jsonable(get_client().tasks.list(**query))


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
    """List issues, optionally scoped to a project."""
    query = dict(filters or {})
    if project is not None:
        query["project"] = _resolve_project_id(project)
    return to_jsonable(get_client().issues.list(**query))


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
    """List epics, optionally scoped to a project."""
    query = dict(filters or {})
    if project is not None:
        query["project"] = _resolve_project_id(project)
    return to_jsonable(get_client().epics.list(**query))


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


@mcp.tool
def list_epic_user_stories(epic: int) -> list[dict[str, Any]]:
    """List the user stories linked to an epic, in their epic ordering."""
    return to_jsonable(get_client().epics.get(epic).list_related_user_stories())


@mcp.tool
def add_user_story_to_epic(epic: int, user_story: int) -> dict[str, Any]:
    """Link an existing user story to an epic. Both ids are numeric ids, not refs."""
    return to_jsonable(get_client().epics.get(epic).add_user_story(user_story))


@mcp.tool
def remove_user_story_from_epic(epic: int, user_story: int) -> dict[str, str]:
    """Unlink a user story from an epic. The user story itself is not deleted."""
    get_client().epics.get(epic).remove_user_story(user_story)
    return {"status": "removed", "epic": str(epic), "user_story": str(user_story)}


# --- Milestones (sprints) -----------------------------------------------------------------


@mcp.tool
def list_milestones(project: str | int, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """List milestones (sprints) of a project."""
    pid = _resolve_project_id(project)
    query = dict(filters or {})
    query["project"] = pid
    return to_jsonable(get_client().milestones.list(**query))


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
    """List wiki pages of a project."""
    pid = _resolve_project_id(project)
    query = dict(filters or {})
    query["project"] = pid
    return to_jsonable(get_client().wikipages.list(**query))


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
