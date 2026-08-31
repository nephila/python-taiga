# python-taiga
# Copyright 2015 Nephila
# See LICENSE for details.

from __future__ import annotations

from typing import Any, Literal

from mcp.server.mcpserver import MCPServer

from .auth import get_client
from .serialize import to_jsonable

mcp = MCPServer(
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

_REF_METHOD = {
    "user_story": "get_userstory_by_ref",
    "task": "get_task_by_ref",
    "issue": "get_issue_by_ref",
    "epic": "get_epic_by_ref",
}


def _resolve_project_id(project: str | int) -> int:
    if isinstance(project, int) or str(project).isdigit():
        return int(project)
    client = get_client()
    return client.projects.get_by_slug(str(project)).id


def _resolve_project(project: str | int) -> Any:
    """Fetch the full Project resource.

    Ref-based lookups need the project's id *and* slug, so (unlike
    `_resolve_project_id`) this always fetches the project even when given a
    numeric id.
    """
    client = get_client()
    if isinstance(project, int) or str(project).isdigit():
        return client.projects.get(int(project))
    return client.projects.get_by_slug(str(project))


def _get_by_ref(entity_type: str, project: str | int, ref: int) -> Any:
    """Resolve a user_story/task/issue/epic to its resource via its per-project ref number.

    `ref` is the sequential number Taiga shows per project - e.g. the 45634 in
    `.../issues/45634` - not the database id used internally for update/delete.
    """
    proj = _resolve_project(project)
    return getattr(proj, _REF_METHOD[entity_type])(ref)


DEFAULT_PAGE_SIZE = 100


def _paginated(query: dict[str, Any]) -> dict[str, Any]:
    """Default a list query to a single bounded page.

    The underlying client only stops auto-fetching subsequent pages once an explicit
    `page` is given — `page_size` alone does not limit it — so a caller that omits
    `page` would otherwise silently walk and return the *entire* remote collection,
    which for large projects can mean tens of thousands of records in one response.
    Pass `page`/`page_size` inside `filters` to move through further pages.

    `filters` is forwarded straight into `ListResource.list()`, so a caller could
    otherwise defeat this bound by passing `pagination=False` (a client-control kwarg,
    stripped here) or an explicit but falsy `page`/`page_size` (e.g. `None` or `0`,
    normalized here rather than left as-is like `dict.setdefault` would).
    """
    query.pop("pagination", None)
    if not query.get("page"):
        query["page"] = 1
    if not query.get("page_size"):
        query["page_size"] = DEFAULT_PAGE_SIZE
    return query


@mcp.tool()
def whoami() -> dict[str, Any]:
    """Return the Taiga user currently authenticated."""
    return to_jsonable(get_client().me())


@mcp.tool()
def list_projects(member: int | None = None, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """List projects visible to the authenticated user, optionally filtered by member id.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.
    """
    query = dict(filters or {})
    if member is not None:
        query["member"] = member
    return to_jsonable(get_client().projects.list(**_paginated(query)))


@mcp.tool()
def get_project(project: str | int) -> dict[str, Any]:
    """Get full project detail by numeric id or slug, including statuses/priorities/severities/points."""
    client = get_client()
    if isinstance(project, int) or str(project).isdigit():
        return to_jsonable(client.projects.get(int(project)))
    return to_jsonable(client.projects.get_by_slug(str(project)))


@mcp.tool()
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


@mcp.tool()
def add_comment(
    entity_type: Literal["user_story", "task", "issue", "epic"], project: str | int, ref: int, comment: str
) -> dict[str, Any]:
    """Add a comment to a user story, task, issue or epic identified by its per-project ref number."""
    # CommentableResource.add_comment() delegates to update(), which returns the stale
    # pre-comment resource with only `version` refreshed - not the comment itself - so it
    # must not be serialized as the result; return an explicit acknowledgement instead.
    resource = _get_by_ref(entity_type, project, ref)
    resource.add_comment(comment)
    return {"status": "commented", "ref": str(ref), "comment": comment}


@mcp.tool()
def add_comment_by_id(
    entity_type: Literal["user_story", "task", "issue", "epic"], id: int, comment: str
) -> dict[str, Any]:  # noqa: A002
    """Add a comment by database id.

    Secondary lookup: prefer `add_comment` with a project + ref (the number shown in the
    Taiga UI/URL). Use this only when you already hold the raw database id.
    """
    client = get_client()
    resource = getattr(client, _ENTITY_ATTR[entity_type]).get(id)
    resource.add_comment(comment)
    return {"status": "commented", "id": str(id), "comment": comment}


_HISTORY_ENTITY_TYPES = ("user_story", "task", "issue", "epic", "wiki")


@mcp.tool()
def get_history(
    entity_type: Literal["user_story", "task", "issue", "epic", "wiki"],
    project: str | int | None,
    ref: int,
) -> list[dict[str, Any]]:
    """Get the full change/comment history of a user story, task, issue, epic or wiki page.

    For entity_type in user_story/task/issue/epic, identify the entity by its per-project
    `ref` number (the one shown in the Taiga UI/URL) plus `project`. Wiki pages have no ref
    number in Taiga - for entity_type="wiki", pass the page's database id as `ref` and omit
    `project`.

    Each entry has a `comment` field (empty string for pure field-change events, non-empty
    for an actual comment) and `delete_comment_date` (non-null if the comment was deleted).
    """
    if entity_type != "wiki" and project is None:
        raise ValueError("project is required unless entity_type is 'wiki'")
    client = get_client()
    if entity_type == "wiki":
        return to_jsonable(client.history.wiki.get(ref))
    resource = _get_by_ref(entity_type, project, ref)
    return to_jsonable(getattr(client.history, entity_type).get(resource.id))


@mcp.tool()
def get_history_by_id(
    entity_type: Literal["user_story", "task", "issue", "epic", "wiki"], id: int  # noqa: A002
) -> list[dict[str, Any]]:
    """Get history by database id.

    Secondary lookup: prefer `get_history` with a project + ref (the number shown in the
    Taiga UI/URL). Use this only when you already hold the raw database id.
    """
    client = get_client()
    return to_jsonable(getattr(client.history, entity_type).get(id))


# --- User stories -----------------------------------------------------------------


@mcp.tool()
def list_user_stories(project: str | int | None = None, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """List user stories, optionally scoped to a project and/or filtered by extra query params.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.
    """
    query = dict(filters or {})
    if project is not None:
        query["project"] = _resolve_project_id(project)
    return to_jsonable(get_client().user_stories.list(**_paginated(query)))


@mcp.tool()
def get_user_story(project: str | int, ref: int) -> dict[str, Any]:
    """Get a user story by its per-project ref number (the number shown in the Taiga UI/URL)."""
    return to_jsonable(_get_by_ref("user_story", project, ref))


@mcp.tool()
def get_user_story_by_id(id: int) -> dict[str, Any]:  # noqa: A002
    """Get a user story by its database id.

    Secondary lookup: prefer `get_user_story` with a project + ref. Use this only when you
    already hold the raw database id, not the ref shown in the Taiga UI/URL.
    """
    return to_jsonable(get_client().user_stories.get(id))


@mcp.tool()
def create_user_story(project: str | int, subject: str, fields: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a user story. `fields` may set status, points, milestone, description, tags, etc."""
    pid = _resolve_project_id(project)
    return to_jsonable(get_client().user_stories.create(pid, subject, **(fields or {})))


@mcp.tool()
def update_user_story(project: str | int, ref: int, fields: dict[str, Any]) -> dict[str, Any]:
    """Update a user story identified by its per-project ref number. `fields` is a dict of the attributes to change."""
    # InstanceResource.patch() only refreshes `version` on the local object, not the other
    # fields the server actually applied, so the result must be re-fetched, not serialized
    # from the patched object itself.
    resource = _get_by_ref("user_story", project, ref)
    resource.patch(list(fields.keys()), **fields)
    return to_jsonable(get_client().user_stories.get(resource.id))


@mcp.tool()
def update_user_story_by_id(id: int, fields: dict[str, Any]) -> dict[str, Any]:  # noqa: A002
    """Update a user story by its database id. Secondary lookup - prefer `update_user_story` with a project + ref."""
    client = get_client()
    resource = client.user_stories.get(id)
    resource.patch(list(fields.keys()), **fields)
    return to_jsonable(client.user_stories.get(id))


@mcp.tool()
def delete_user_story(project: str | int, ref: int) -> dict[str, str]:
    """Delete a user story identified by its per-project ref number."""
    resource = _get_by_ref("user_story", project, ref)
    resource.delete()
    return {"status": "deleted", "ref": str(ref)}


@mcp.tool()
def delete_user_story_by_id(id: int) -> dict[str, str]:  # noqa: A002
    """Delete a user story by its database id. Secondary lookup - prefer `delete_user_story` with a project + ref."""
    get_client().user_stories.delete(id)
    return {"status": "deleted", "id": str(id)}


# --- Tasks --------------------------------------------------------------------------


@mcp.tool()
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


@mcp.tool()
def get_task(project: str | int, ref: int) -> dict[str, Any]:
    """Get a task by its per-project ref number (the number shown in the Taiga UI/URL)."""
    return to_jsonable(_get_by_ref("task", project, ref))


@mcp.tool()
def get_task_by_id(id: int) -> dict[str, Any]:  # noqa: A002
    """Get a task by its database id.

    Secondary lookup: prefer `get_task` with a project + ref. Use this only when you
    already hold the raw database id, not the ref shown in the Taiga UI/URL.
    """
    return to_jsonable(get_client().tasks.get(id))


@mcp.tool()
def create_task(project: str | int, subject: str, status: int, fields: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a task. `status` is the numeric task-status id (see get_project). `fields` may set user_story, etc."""
    pid = _resolve_project_id(project)
    return to_jsonable(get_client().tasks.create(pid, subject, status, **(fields or {})))


@mcp.tool()
def update_task(project: str | int, ref: int, fields: dict[str, Any]) -> dict[str, Any]:
    """Update a task identified by its per-project ref number. `fields` is a dict of the attributes to change."""
    # See update_user_story: patch() doesn't refresh the local object, so re-fetch it.
    resource = _get_by_ref("task", project, ref)
    resource.patch(list(fields.keys()), **fields)
    return to_jsonable(get_client().tasks.get(resource.id))


@mcp.tool()
def update_task_by_id(id: int, fields: dict[str, Any]) -> dict[str, Any]:  # noqa: A002
    """Update a task by its database id. Secondary lookup - prefer `update_task` with a project + ref."""
    client = get_client()
    resource = client.tasks.get(id)
    resource.patch(list(fields.keys()), **fields)
    return to_jsonable(client.tasks.get(id))


@mcp.tool()
def delete_task(project: str | int, ref: int) -> dict[str, str]:
    """Delete a task identified by its per-project ref number."""
    resource = _get_by_ref("task", project, ref)
    resource.delete()
    return {"status": "deleted", "ref": str(ref)}


@mcp.tool()
def delete_task_by_id(id: int) -> dict[str, str]:  # noqa: A002
    """Delete a task by its database id. Secondary lookup - prefer `delete_task` with a project + ref."""
    get_client().tasks.delete(id)
    return {"status": "deleted", "id": str(id)}


# --- Issues ---------------------------------------------------------------------------


@mcp.tool()
def list_issues(project: str | int | None = None, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """List issues, optionally scoped to a project.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.
    """
    query = dict(filters or {})
    if project is not None:
        query["project"] = _resolve_project_id(project)
    return to_jsonable(get_client().issues.list(**_paginated(query)))


@mcp.tool()
def get_issue(project: str | int, ref: int) -> dict[str, Any]:
    """Get an issue by its per-project ref number (the number shown in the Taiga UI/URL, e.g. .../issues/45634)."""
    return to_jsonable(_get_by_ref("issue", project, ref))


@mcp.tool()
def get_issue_by_id(id: int) -> dict[str, Any]:  # noqa: A002
    """Get an issue by its database id.

    Secondary lookup: prefer `get_issue` with a project + ref. Use this only when you
    already hold the raw database id, not the ref shown in the Taiga UI/URL.
    """
    return to_jsonable(get_client().issues.get(id))


@mcp.tool()
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


@mcp.tool()
def update_issue(project: str | int, ref: int, fields: dict[str, Any]) -> dict[str, Any]:
    """Update an issue identified by its per-project ref number. `fields` is a dict of the attributes to change."""
    # See update_user_story: patch() doesn't refresh the local object, so re-fetch it.
    resource = _get_by_ref("issue", project, ref)
    resource.patch(list(fields.keys()), **fields)
    return to_jsonable(get_client().issues.get(resource.id))


@mcp.tool()
def update_issue_by_id(id: int, fields: dict[str, Any]) -> dict[str, Any]:  # noqa: A002
    """Update an issue by its database id. Secondary lookup - prefer `update_issue` with a project + ref."""
    client = get_client()
    resource = client.issues.get(id)
    resource.patch(list(fields.keys()), **fields)
    return to_jsonable(client.issues.get(id))


@mcp.tool()
def delete_issue(project: str | int, ref: int) -> dict[str, str]:
    """Delete an issue identified by its per-project ref number."""
    resource = _get_by_ref("issue", project, ref)
    resource.delete()
    return {"status": "deleted", "ref": str(ref)}


@mcp.tool()
def delete_issue_by_id(id: int) -> dict[str, str]:  # noqa: A002
    """Delete an issue by its database id. Secondary lookup - prefer `delete_issue` with a project + ref."""
    get_client().issues.delete(id)
    return {"status": "deleted", "id": str(id)}


# --- Epics ------------------------------------------------------------------------------


@mcp.tool()
def list_epics(project: str | int | None = None, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """List epics, optionally scoped to a project.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.
    """
    query = dict(filters or {})
    if project is not None:
        query["project"] = _resolve_project_id(project)
    return to_jsonable(get_client().epics.list(**_paginated(query)))


@mcp.tool()
def get_epic(project: str | int, ref: int) -> dict[str, Any]:
    """Get an epic by its per-project ref number (the number shown in the Taiga UI/URL)."""
    return to_jsonable(_get_by_ref("epic", project, ref))


@mcp.tool()
def get_epic_by_id(id: int) -> dict[str, Any]:  # noqa: A002
    """Get an epic by its database id.

    Secondary lookup: prefer `get_epic` with a project + ref. Use this only when you
    already hold the raw database id, not the ref shown in the Taiga UI/URL.
    """
    return to_jsonable(get_client().epics.get(id))


@mcp.tool()
def create_epic(project: str | int, subject: str, fields: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create an epic."""
    pid = _resolve_project_id(project)
    return to_jsonable(get_client().epics.create(pid, subject, **(fields or {})))


@mcp.tool()
def update_epic(project: str | int, ref: int, fields: dict[str, Any]) -> dict[str, Any]:
    """Update an epic identified by its per-project ref number. `fields` is a dict of the attributes to change."""
    # See update_user_story: patch() doesn't refresh the local object, so re-fetch it.
    resource = _get_by_ref("epic", project, ref)
    resource.patch(list(fields.keys()), **fields)
    return to_jsonable(get_client().epics.get(resource.id))


@mcp.tool()
def update_epic_by_id(id: int, fields: dict[str, Any]) -> dict[str, Any]:  # noqa: A002
    """Update an epic by its database id. Secondary lookup - prefer `update_epic` with a project + ref."""
    client = get_client()
    resource = client.epics.get(id)
    resource.patch(list(fields.keys()), **fields)
    return to_jsonable(client.epics.get(id))


@mcp.tool()
def delete_epic(project: str | int, ref: int) -> dict[str, str]:
    """Delete an epic identified by its per-project ref number."""
    resource = _get_by_ref("epic", project, ref)
    resource.delete()
    return {"status": "deleted", "ref": str(ref)}


@mcp.tool()
def delete_epic_by_id(id: int) -> dict[str, str]:  # noqa: A002
    """Delete an epic by its database id. Secondary lookup - prefer `delete_epic` with a project + ref."""
    get_client().epics.delete(id)
    return {"status": "deleted", "id": str(id)}


# --- Milestones (sprints) -----------------------------------------------------------------


@mcp.tool()
def list_milestones(project: str | int, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """List milestones (sprints) of a project.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.
    """
    pid = _resolve_project_id(project)
    query = dict(filters or {})
    query["project"] = pid
    return to_jsonable(get_client().milestones.list(**_paginated(query)))


@mcp.tool()
def get_milestone(id: int) -> dict[str, Any]:  # noqa: A002
    """Get a milestone by id."""
    return to_jsonable(get_client().milestones.get(id))


@mcp.tool()
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


@mcp.tool()
def delete_milestone(id: int) -> dict[str, str]:  # noqa: A002
    """Delete a milestone by id."""
    get_client().milestones.delete(id)
    return {"status": "deleted", "id": str(id)}


# --- Wiki pages -----------------------------------------------------------------------------


@mcp.tool()
def list_wiki_pages(project: str | int, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """List wiki pages of a project.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.
    """
    pid = _resolve_project_id(project)
    query = dict(filters or {})
    query["project"] = pid
    return to_jsonable(get_client().wikipages.list(**_paginated(query)))


@mcp.tool()
def get_wiki_page(id: int) -> dict[str, Any]:  # noqa: A002
    """Get a wiki page by id."""
    return to_jsonable(get_client().wikipages.get(id))


@mcp.tool()
def create_wiki_page(
    project: str | int, slug: str, content: str, fields: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Create a wiki page."""
    pid = _resolve_project_id(project)
    return to_jsonable(get_client().wikipages.create(pid, slug, content, **(fields or {})))


@mcp.tool()
def update_wiki_page(id: int, fields: dict[str, Any]) -> dict[str, Any]:  # noqa: A002
    """Update a wiki page. `fields` is a dict of the attributes to change."""
    # See update_user_story: patch() doesn't refresh the local object, so re-fetch it.
    client = get_client()
    resource = client.wikipages.get(id)
    resource.patch(list(fields.keys()), **fields)
    return to_jsonable(client.wikipages.get(id))
