# python-taiga
# Copyright 2015 Nephila
# See LICENSE for details.

from __future__ import annotations

from typing import Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from .auth import get_client
from .serialize import apply_payload, to_jsonable

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
    return _get_by_ref_in(_resolve_project(project), entity_type, ref)


def _get_by_ref_in(proj: Any, entity_type: str, ref: int) -> Any:
    """Like `_get_by_ref`, but for an already-resolved project (avoids a re-fetch per item)."""
    return getattr(proj, _REF_METHOD[entity_type])(ref)


def _represent(
    resource: Any,
    written: dict[str, Any],
    return_representation: str,
) -> dict[str, Any]:
    """Project a written resource down per return_representation - "minimal"/"none" only.

    Callers handle "full" themselves: that shape differs between create_* (no re-fetch)
    and update_* (re-fetch required), and duplicating that branching here would obscure,
    not simplify, either.
    """
    base: dict[str, Any] = {"id": resource.id, "version": getattr(resource, "version", None)}
    if hasattr(resource, "ref"):
        base["ref"] = resource.ref
    if return_representation == "minimal":
        return {**written, **base}
    return {"ok": True, **base}


def _with_version(resource: Any, fields: dict[str, Any]) -> dict[str, Any]:
    """Return `fields` with the resource's current `version` added when the caller omitted it.

    The resource was just fetched, so its version is the optimistic-lock token Taiga expects;
    leaving it out makes Taiga reject the write. An explicit caller-supplied `version` wins.
    """
    version = getattr(resource, "version", None)
    if "version" in fields or not isinstance(version, int):
        return fields
    return {**fields, "version": version}


def _patch(resource: Any, fields: dict[str, Any]) -> None:
    """Apply `resource.patch()`, surfacing the real failure message to the caller.

    Any exception here (a stale/missing `version`, a resource that vanished after
    lookup, ...) would otherwise reach the caller as a bare "Error executing tool
    <name>" - the mcp SDK replaces any exception that isn't its own `ToolError`
    with a fixed generic message, deliberately, treating it as an unanticipated
    crash. Re-raising as `ToolError` preserves the real message, the same detail
    `update_work_items` already surfaces per-row for the same underlying failures.
    """
    fields = _with_version(resource, fields)
    try:
        resource.patch(list(fields.keys()), **fields)
    except Exception as exc:
        raise ToolError(f"{type(exc).__name__}: {exc}") from exc


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


_FILTER_TRAP_KEYS = frozenset(
    {"payload", "fields", "strip_media", "expand", "strict_filters", "include_user_stories", "resolve_assigned_users"}
)


def _check_strict_filters(filters: dict[str, Any] | None, strict_filters: bool) -> None:
    """Raise if `filters` nests one of this server's own parameter names by mistake.

    Taiga's REST backend silently ignores unknown query parameters, so a caller who nests
    e.g. `filters={"include_user_stories": False}` instead of passing it top-level gets a
    full, unfiltered response with no error - a measured 24x size regression with no
    signal either way. Checked against a fixed set of this server's own parameter names,
    not Taiga's full (and from this client, unknowable) set of real filterable fields, so
    this can never false-positive on a genuine Taiga filter.

    Raises `ToolError`, not a bare `ValueError` - the mcp SDK discards a bare exception's
    message and replaces it with a generic "Error executing tool <name>", which would
    defeat the entire point of naming the offending key(s) here.
    """
    if not strict_filters or not filters:
        return
    trapped = _FILTER_TRAP_KEYS & filters.keys()
    if trapped:
        raise ToolError(
            f"filters contains parameter name(s) meant to be passed top-level, not nested: {sorted(trapped)}"
        )


@mcp.tool()
def whoami() -> dict[str, Any]:
    """Return the Taiga user currently authenticated."""
    return to_jsonable(get_client().me())


@mcp.tool()
def list_projects(
    member: int | None = None,
    filters: dict[str, Any] | None = None,
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
    strict_filters: bool = False,
) -> list[dict[str, Any]]:
    """List projects visible to the authenticated user, optionally filtered by member id.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics. `strict_filters=True` raises instead of silently
    ignoring a `filters` key that collides with this tool's own parameter names.
    """
    _check_strict_filters(filters, strict_filters)
    query = dict(filters or {})
    if member is not None:
        query["member"] = member
    result = to_jsonable(get_client().projects.list(**_paginated(query)))
    return apply_payload(result, "project", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


@mcp.tool()
def get_project(
    project: str | int,
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
) -> dict[str, Any]:
    """Get full project detail by numeric id or slug, including statuses/priorities/severities/points.

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics.
    """
    client = get_client()
    if isinstance(project, int) or str(project).isdigit():
        result = to_jsonable(client.projects.get(int(project)))
    else:
        result = to_jsonable(client.projects.get_by_slug(str(project)))
    return apply_payload(result, "project", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


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
def list_memberships(
    project: str | int,
    filters: dict[str, Any] | None = None,
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
    strict_filters: bool = False,
) -> list[dict[str, Any]]:
    """List a project's memberships (username, full_name, user_email, role_name, etc.) -
    the pool of users assignable as owner/assigned_to/watcher on that project's items.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further.

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics. `strict_filters=True` raises instead of silently
    ignoring a `filters` key that collides with this tool's own parameter names.
    """
    _check_strict_filters(filters, strict_filters)
    proj = _resolve_project(project)
    query = _paginated(dict(filters or {}))
    result = to_jsonable(proj.list_memberships(**query))
    return apply_payload(result, "membership", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


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
    ref: int,
    project: str | int | None = None,
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
    entity_type: Literal["user_story", "task", "issue", "epic", "wiki"],
    id: int,  # noqa: A002
) -> list[dict[str, Any]]:
    """Get history by database id.

    Secondary lookup: prefer `get_history` with a project + ref (the number shown in the
    Taiga UI/URL). Use this only when you already hold the raw database id.
    """
    client = get_client()
    return to_jsonable(getattr(client.history, entity_type).get(id))


@mcp.tool()
def get_custom_attributes_values(
    entity_type: Literal["user_story", "task", "issue", "epic"],
    project: str | int,
    ref: int,
) -> dict[str, Any]:
    """Get the custom-attribute values of a user story, task, issue or epic,
    identified by its per-project ref number. Keys of `attributes_values` are
    attribute ids as strings - see get_project's `*_custom_attributes` lists
    for id -> name. The returned `version` belongs to this custom-attributes-
    values resource, a separate version sequence from the entity's own
    `version` field - pass it back to `set_custom_attribute_value`, not the
    entity's version.
    """
    resource = _get_by_ref(entity_type, project, ref)
    return to_jsonable(resource.get_attributes())


@mcp.tool()
def get_custom_attributes_values_by_id(
    entity_type: Literal["user_story", "task", "issue", "epic"],
    id: int,  # noqa: A002
) -> dict[str, Any]:
    """Get custom-attribute values by database id.

    Secondary lookup: prefer `get_custom_attributes_values` with a project + ref.
    Use this only when you already hold the raw database id.
    """
    client = get_client()
    resource = getattr(client, _ENTITY_ATTR[entity_type]).get(id)
    return to_jsonable(resource.get_attributes())


@mcp.tool()
def set_custom_attribute_value(
    entity_type: Literal["user_story", "task", "issue", "epic"],
    project: str | int,
    ref: int,
    attribute_id: int,
    value: Any,
    version: int | None = None,
) -> dict[str, Any]:
    """Set one custom-attribute value on a user story, task, issue or epic,
    identified by its per-project ref number. `attribute_id` is the numeric id
    from get_project's `*_custom_attributes` list (e.g. the "Code" attribute).
    `version` is optional: when omitted, the custom-attributes-values resource's
    current version is used. If given, it is that resource's own version (from a
    prior get_custom_attributes_values call) - not the entity's own `version` field.
    """
    resource = _get_by_ref(entity_type, project, ref)
    return to_jsonable(resource.set_attribute(attribute_id, value, version=version))


@mcp.tool()
def set_custom_attribute_value_by_id(
    entity_type: Literal["user_story", "task", "issue", "epic"],
    id: int,  # noqa: A002
    attribute_id: int,
    value: Any,
    version: int | None = None,
) -> dict[str, Any]:
    """Set a custom-attribute value by database id.

    Secondary lookup: prefer `set_custom_attribute_value` with a project + ref.
    Use this only when you already hold the raw database id.
    """
    client = get_client()
    resource = getattr(client, _ENTITY_ATTR[entity_type]).get(id)
    return to_jsonable(resource.set_attribute(attribute_id, value, version=version))


def _membership_names(proj: Any, wanted: set[int]) -> dict[int, str | None]:
    """Map user id -> full_name over a project's memberships, paging until `wanted` is covered."""
    names: dict[int, str | None] = {}
    page = 1
    while True:
        batch = to_jsonable(proj.list_memberships(page=page, page_size=DEFAULT_PAGE_SIZE))
        names.update({m["user"]: m.get("full_name") for m in batch})
        if len(batch) < DEFAULT_PAGE_SIZE or wanted <= names.keys():
            return names
        page += 1


def _resolve_assigned_users(
    data: dict[str, Any] | list[dict[str, Any]],
) -> dict[str, Any] | list[dict[str, Any]]:
    """Attach `assigned_users_extra_info` (id + full_name_display) to each item's bare
    `assigned_users` id list, resolving names via each distinct project's memberships.

    Membership records use `full_name` for the display name, not the `full_name_display`
    field seen on other Taiga user blocks (`owner_extra_info`, `assigned_to_extra_info`,
    ...) - confirmed against a live instance. We still key our own output as
    `full_name_display`, for consistency with those other blocks; only the source field
    read from the membership record differs. Pages through each distinct referenced
    project's memberships until every assigned user id is found or the pages run out.
    """
    items = data if isinstance(data, list) else [data]
    if not any(item.get("assigned_users") for item in items):
        return data
    client = get_client()
    membership_maps: dict[int, dict[int, str | None]] = {}
    for item in items:
        assigned_users = item.get("assigned_users")
        if not assigned_users:
            continue
        project_id = item["project"]
        if project_id not in membership_maps:
            wanted = {uid for it in items if it.get("project") == project_id for uid in it.get("assigned_users") or []}
            membership_maps[project_id] = _membership_names(client.projects.get(project_id), wanted)
        name_map = membership_maps[project_id]
        item["assigned_users_extra_info"] = [
            {"id": uid, "full_name_display": name_map.get(uid)} for uid in assigned_users
        ]
    return data


# --- User stories -----------------------------------------------------------------


@mcp.tool()
def list_user_stories(
    project: str | int | None = None,
    filters: dict[str, Any] | None = None,
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
    resolve_assigned_users: bool = False,
    strict_filters: bool = False,
) -> list[dict[str, Any]]:
    """List user stories, optionally scoped to a project and/or filtered by extra query params.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics. `resolve_assigned_users=True` attaches
    `assigned_users_extra_info` (costs an extra API call per project) - see docs/mcp.rst.
    `strict_filters=True` raises instead of silently ignoring a `filters` key that collides
    with this tool's own parameter names.
    """
    _check_strict_filters(filters, strict_filters)
    query = dict(filters or {})
    if project is not None:
        query["project"] = _resolve_project_id(project)
    result = to_jsonable(get_client().user_stories.list(**_paginated(query)))
    if resolve_assigned_users:
        result = _resolve_assigned_users(result)
    return apply_payload(result, "userstory", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


@mcp.tool()
def get_user_story(
    project: str | int,
    ref: int,
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
    resolve_assigned_users: bool = False,
) -> dict[str, Any]:
    """Get a user story by its per-project ref number (the number shown in the Taiga UI/URL).

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics. `resolve_assigned_users=True` attaches
    `assigned_users_extra_info` (costs an extra API call per project) - see docs/mcp.rst.
    """
    result = to_jsonable(_get_by_ref("user_story", project, ref))
    if resolve_assigned_users:
        result = _resolve_assigned_users(result)
    return apply_payload(result, "userstory", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


@mcp.tool()
def get_user_story_by_id(
    id: int,  # noqa: A002
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
    resolve_assigned_users: bool = False,
) -> dict[str, Any]:
    """Get a user story by its database id.

    Secondary lookup: prefer `get_user_story` with a project + ref. Use this only when you
    already hold the raw database id, not the ref shown in the Taiga UI/URL.

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics. `resolve_assigned_users=True` attaches
    `assigned_users_extra_info` (costs an extra API call per project) - see docs/mcp.rst.
    """
    result = to_jsonable(get_client().user_stories.get(id))
    if resolve_assigned_users:
        result = _resolve_assigned_users(result)
    return apply_payload(result, "userstory", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


@mcp.tool()
def create_user_story(
    project: str | int,
    subject: str,
    fields: dict[str, Any] | None = None,
    return_representation: Literal["full", "minimal", "none"] = "full",
) -> dict[str, Any]:
    """Create a user story. `fields` may set status, points, milestone, description, tags, etc.

    `return_representation` ("full" default / "minimal" / "none") controls how much of the
    created resource comes back - "minimal" returns just id/ref/version plus whatever was
    in `fields`; "none" returns only an acknowledgement. See docs/mcp.rst for the exact shape.
    """
    pid = _resolve_project_id(project)
    resource = get_client().user_stories.create(pid, subject, **(fields or {}))
    if return_representation == "full":
        return to_jsonable(resource)
    return _represent(resource, fields or {}, return_representation)


@mcp.tool()
def update_user_story(
    project: str | int,
    ref: int,
    fields: dict[str, Any],
    return_representation: Literal["full", "minimal", "none"] = "full",
) -> dict[str, Any]:
    """Update a user story identified by its per-project ref number. `fields` is a dict of the attributes to change.

    `return_representation` ("full" default / "minimal" / "none") controls how much of the
    updated resource comes back. "full" re-fetches the complete resource, exactly as before -
    InstanceResource.patch() only refreshes `version` on the local object, not the other
    fields the server actually applied, so "full" must re-fetch, not serialize from the
    patched object itself. "minimal"/"none" skip that re-fetch entirely - they only need
    id/ref/version (already on the patched-in-place resource) and, for "minimal", the
    caller's own `fields` (already known). See docs/mcp.rst.
    """
    resource = _get_by_ref("user_story", project, ref)
    _patch(resource, fields)
    if return_representation == "full":
        return to_jsonable(get_client().user_stories.get(resource.id))
    return _represent(resource, fields, return_representation)


@mcp.tool()
def update_user_story_by_id(
    id: int,  # noqa: A002
    fields: dict[str, Any],
    return_representation: Literal["full", "minimal", "none"] = "full",
) -> dict[str, Any]:
    """Update a user story by its database id. Secondary lookup - prefer `update_user_story` with a project + ref.

    `return_representation` ("full" default / "minimal" / "none") - see `update_user_story`
    for the full explanation; "minimal"/"none" skip the re-fetch this tool otherwise performs.
    """
    client = get_client()
    resource = client.user_stories.get(id)
    _patch(resource, fields)
    if return_representation == "full":
        return to_jsonable(client.user_stories.get(id))
    return _represent(resource, fields, return_representation)


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
    project: str | int | None = None,
    user_story: int | None = None,
    filters: dict[str, Any] | None = None,
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
    strict_filters: bool = False,
) -> list[dict[str, Any]]:
    """List tasks, optionally scoped to a project and/or a user story.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics. `strict_filters=True` raises instead of silently
    ignoring a `filters` key that collides with this tool's own parameter names.
    """
    _check_strict_filters(filters, strict_filters)
    query = dict(filters or {})
    if project is not None:
        query["project"] = _resolve_project_id(project)
    if user_story is not None:
        query["user_story"] = user_story
    result = to_jsonable(get_client().tasks.list(**_paginated(query)))
    return apply_payload(result, "task", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


@mcp.tool()
def get_task(
    project: str | int,
    ref: int,
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
) -> dict[str, Any]:
    """Get a task by its per-project ref number (the number shown in the Taiga UI/URL).

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics.
    """
    result = to_jsonable(_get_by_ref("task", project, ref))
    return apply_payload(result, "task", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


@mcp.tool()
def get_task_by_id(
    id: int,  # noqa: A002
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
) -> dict[str, Any]:
    """Get a task by its database id.

    Secondary lookup: prefer `get_task` with a project + ref. Use this only when you
    already hold the raw database id, not the ref shown in the Taiga UI/URL.

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics.
    """
    result = to_jsonable(get_client().tasks.get(id))
    return apply_payload(result, "task", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


@mcp.tool()
def create_task(
    project: str | int,
    subject: str,
    status: int,
    fields: dict[str, Any] | None = None,
    return_representation: Literal["full", "minimal", "none"] = "full",
) -> dict[str, Any]:
    """Create a task. `status` is the numeric task-status id (see get_project). `fields` may set user_story, etc.

    `return_representation` ("full" default / "minimal" / "none") controls how much of the
    created resource comes back - see docs/mcp.rst.
    """
    pid = _resolve_project_id(project)
    resource = get_client().tasks.create(pid, subject, status, **(fields or {}))
    if return_representation == "full":
        return to_jsonable(resource)
    return _represent(resource, fields or {}, return_representation)


@mcp.tool()
def update_task(
    project: str | int,
    ref: int,
    fields: dict[str, Any],
    return_representation: Literal["full", "minimal", "none"] = "full",
) -> dict[str, Any]:
    """Update a task identified by its per-project ref number. `fields` is a dict of the attributes to change.

    `return_representation` ("full" default / "minimal" / "none") - see `update_user_story`
    for the full explanation; "minimal"/"none" skip the re-fetch this tool otherwise performs.
    """
    # See update_user_story: patch() doesn't refresh the local object, so re-fetch it for "full".
    resource = _get_by_ref("task", project, ref)
    _patch(resource, fields)
    if return_representation == "full":
        return to_jsonable(get_client().tasks.get(resource.id))
    return _represent(resource, fields, return_representation)


@mcp.tool()
def update_task_by_id(
    id: int,  # noqa: A002
    fields: dict[str, Any],
    return_representation: Literal["full", "minimal", "none"] = "full",
) -> dict[str, Any]:
    """Update a task by its database id. Secondary lookup - prefer `update_task` with a project + ref.

    `return_representation` ("full" default / "minimal" / "none") - see `update_user_story`
    for the full explanation; "minimal"/"none" skip the re-fetch this tool otherwise performs.
    """
    client = get_client()
    resource = client.tasks.get(id)
    _patch(resource, fields)
    if return_representation == "full":
        return to_jsonable(client.tasks.get(id))
    return _represent(resource, fields, return_representation)


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
def list_issues(
    project: str | int | None = None,
    filters: dict[str, Any] | None = None,
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
    strict_filters: bool = False,
) -> list[dict[str, Any]]:
    """List issues, optionally scoped to a project.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics. `strict_filters=True` raises instead of silently
    ignoring a `filters` key that collides with this tool's own parameter names.
    """
    _check_strict_filters(filters, strict_filters)
    query = dict(filters or {})
    if project is not None:
        query["project"] = _resolve_project_id(project)
    result = to_jsonable(get_client().issues.list(**_paginated(query)))
    return apply_payload(result, "issue", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


@mcp.tool()
def get_issue(
    project: str | int,
    ref: int,
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
) -> dict[str, Any]:
    """Get an issue by its per-project ref number (the number shown in the Taiga UI/URL, e.g. .../issues/45634).

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics.
    """
    result = to_jsonable(_get_by_ref("issue", project, ref))
    return apply_payload(result, "issue", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


@mcp.tool()
def get_issue_by_id(
    id: int,  # noqa: A002
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
) -> dict[str, Any]:
    """Get an issue by its database id.

    Secondary lookup: prefer `get_issue` with a project + ref. Use this only when you
    already hold the raw database id, not the ref shown in the Taiga UI/URL.

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics.
    """
    result = to_jsonable(get_client().issues.get(id))
    return apply_payload(result, "issue", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


@mcp.tool()
def create_issue(
    project: str | int,
    subject: str,
    priority: int,
    status: int,
    issue_type: int,
    severity: int,
    fields: dict[str, Any] | None = None,
    return_representation: Literal["full", "minimal", "none"] = "full",
) -> dict[str, Any]:
    """Create an issue. `priority`/`status`/`issue_type`/`severity` are numeric ids (see get_project).

    `return_representation` ("full" default / "minimal" / "none") controls how much of the
    created resource comes back - see docs/mcp.rst.
    """
    pid = _resolve_project_id(project)
    resource = get_client().issues.create(pid, subject, priority, status, issue_type, severity, **(fields or {}))
    if return_representation == "full":
        return to_jsonable(resource)
    return _represent(resource, fields or {}, return_representation)


@mcp.tool()
def update_issue(
    project: str | int,
    ref: int,
    fields: dict[str, Any],
    return_representation: Literal["full", "minimal", "none"] = "full",
) -> dict[str, Any]:
    """Update an issue identified by its per-project ref number. `fields` is a dict of the attributes to change.

    `return_representation` ("full" default / "minimal" / "none") - see `update_user_story`
    for the full explanation; "minimal"/"none" skip the re-fetch this tool otherwise performs.
    """
    # See update_user_story: patch() doesn't refresh the local object, so re-fetch it for "full".
    resource = _get_by_ref("issue", project, ref)
    _patch(resource, fields)
    if return_representation == "full":
        return to_jsonable(get_client().issues.get(resource.id))
    return _represent(resource, fields, return_representation)


@mcp.tool()
def update_issue_by_id(
    id: int,  # noqa: A002
    fields: dict[str, Any],
    return_representation: Literal["full", "minimal", "none"] = "full",
) -> dict[str, Any]:
    """Update an issue by its database id. Secondary lookup - prefer `update_issue` with a project + ref.

    `return_representation` ("full" default / "minimal" / "none") - see `update_user_story`
    for the full explanation; "minimal"/"none" skip the re-fetch this tool otherwise performs.
    """
    client = get_client()
    resource = client.issues.get(id)
    _patch(resource, fields)
    if return_representation == "full":
        return to_jsonable(client.issues.get(id))
    return _represent(resource, fields, return_representation)


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
def list_epics(
    project: str | int | None = None,
    filters: dict[str, Any] | None = None,
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
    strict_filters: bool = False,
) -> list[dict[str, Any]]:
    """List epics, optionally scoped to a project.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics. `strict_filters=True` raises instead of silently
    ignoring a `filters` key that collides with this tool's own parameter names.
    """
    _check_strict_filters(filters, strict_filters)
    query = dict(filters or {})
    if project is not None:
        query["project"] = _resolve_project_id(project)
    result = to_jsonable(get_client().epics.list(**_paginated(query)))
    return apply_payload(result, "epic", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


@mcp.tool()
def get_epic(
    project: str | int,
    ref: int,
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
) -> dict[str, Any]:
    """Get an epic by its per-project ref number (the number shown in the Taiga UI/URL).

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics.
    """
    result = to_jsonable(_get_by_ref("epic", project, ref))
    return apply_payload(result, "epic", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


@mcp.tool()
def get_epic_by_id(
    id: int,  # noqa: A002
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
) -> dict[str, Any]:
    """Get an epic by its database id.

    Secondary lookup: prefer `get_epic` with a project + ref. Use this only when you
    already hold the raw database id, not the ref shown in the Taiga UI/URL.

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics.
    """
    result = to_jsonable(get_client().epics.get(id))
    return apply_payload(result, "epic", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


@mcp.tool()
def create_epic(
    project: str | int,
    subject: str,
    fields: dict[str, Any] | None = None,
    return_representation: Literal["full", "minimal", "none"] = "full",
) -> dict[str, Any]:
    """Create an epic.

    `return_representation` ("full" default / "minimal" / "none") controls how much of the
    created resource comes back - see docs/mcp.rst.
    """
    pid = _resolve_project_id(project)
    resource = get_client().epics.create(pid, subject, **(fields or {}))
    if return_representation == "full":
        return to_jsonable(resource)
    return _represent(resource, fields or {}, return_representation)


@mcp.tool()
def update_epic(
    project: str | int,
    ref: int,
    fields: dict[str, Any],
    return_representation: Literal["full", "minimal", "none"] = "full",
) -> dict[str, Any]:
    """Update an epic identified by its per-project ref number. `fields` is a dict of the attributes to change.

    `return_representation` ("full" default / "minimal" / "none") - see `update_user_story`
    for the full explanation; "minimal"/"none" skip the re-fetch this tool otherwise performs.
    """
    # See update_user_story: patch() doesn't refresh the local object, so re-fetch it for "full".
    resource = _get_by_ref("epic", project, ref)
    _patch(resource, fields)
    if return_representation == "full":
        return to_jsonable(get_client().epics.get(resource.id))
    return _represent(resource, fields, return_representation)


@mcp.tool()
def update_epic_by_id(
    id: int,  # noqa: A002
    fields: dict[str, Any],
    return_representation: Literal["full", "minimal", "none"] = "full",
) -> dict[str, Any]:
    """Update an epic by its database id. Secondary lookup - prefer `update_epic` with a project + ref.

    `return_representation` ("full" default / "minimal" / "none") - see `update_user_story`
    for the full explanation; "minimal"/"none" skip the re-fetch this tool otherwise performs.
    """
    client = get_client()
    resource = client.epics.get(id)
    _patch(resource, fields)
    if return_representation == "full":
        return to_jsonable(client.epics.get(id))
    return _represent(resource, fields, return_representation)


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


def _link_epic(epic: Any, user_story_id: int) -> dict[str, Any]:
    """Link a user story to an epic, surfacing the real failure message to the caller (see `_patch`)."""
    try:
        return to_jsonable(epic.add_related_user_story(user_story_id))
    except Exception as exc:
        raise ToolError(f"{type(exc).__name__}: {exc}") from exc


@mcp.tool()
def link_epic_user_story(project: str | int, epic_ref: int, user_story_ref: int) -> dict[str, Any]:
    """Link a user story to an epic, identifying both by their per-project ref numbers."""
    proj = _resolve_project(project)
    epic = proj.get_epic_by_ref(epic_ref)
    user_story = proj.get_userstory_by_ref(user_story_ref)
    return _link_epic(epic, user_story.id)


@mcp.tool()
def link_epic_user_story_by_id(epic_id: int, user_story_id: int) -> dict[str, Any]:
    """Link a user story to an epic by their database ids.

    Secondary lookup: prefer `link_epic_user_story` with a project + ref numbers.
    """
    client = get_client()
    epic = client.epics.get(epic_id)
    return _link_epic(epic, user_story_id)


@mcp.tool()
def update_work_items(
    project: str | int,
    updates: list[dict[str, Any]],
    return_representation: Literal["full", "minimal", "none"] = "full",
) -> list[dict[str, Any]]:
    """Update a batch of user stories/tasks/issues/epics in one call.

    Each entry in `updates` is `{"entity_type": "user_story"|"task"|"issue"|"epic", "ref": <int>,
    "fields": {...}}` - `ref` is the per-project ref number (as in `update_user_story` etc.), and
    `fields` is the dict of attributes to change, exactly as a single-item `update_*` call would
    take it. If `version` is omitted from an item's `fields`, the fetched item's current version
    is used for optimistic locking; an explicit `version` wins.

    Not atomic: items are processed in order, each succeeds or fails independently, and a
    failure does not roll back or block any other item. Returns one result row per input item,
    in the same order, so `updates` and the result can always be zipped. A successful item's row
    follows `return_representation` exactly like a single-item `update_*` call. A failed item's
    row is `{"status": "error", "entity_type": ..., "ref": ..., "error": "<message>"}`.

    Wiki pages are not supported here - they have no per-project ref number, and aren't part of
    the sprint-rollover workflow this tool targets. Use `update_wiki_page` directly.
    """
    results: list[dict[str, Any]] = []
    proj = _resolve_project(project) if updates else None
    for item in updates:
        try:
            entity_type = item["entity_type"]
            ref = item["ref"]
            fields = item["fields"]
            resource = _get_by_ref_in(proj, entity_type, ref)
            patch_fields = _with_version(resource, fields)
            resource.patch(list(patch_fields.keys()), **patch_fields)
            if return_representation == "full":
                client_attr = getattr(get_client(), _ENTITY_ATTR[entity_type])
                results.append(to_jsonable(client_attr.get(resource.id)))
            else:
                results.append(_represent(resource, fields, return_representation))
        except Exception as exc:  # A single bad item must not abort the rest of the batch.
            results.append(
                {
                    "status": "error",
                    "entity_type": item.get("entity_type"),
                    "ref": item.get("ref"),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
    return results


# --- Milestones (sprints) -----------------------------------------------------------------


def _strip_user_stories(
    data: dict[str, Any] | list[dict[str, Any]],
) -> dict[str, Any] | list[dict[str, Any]]:
    """Drop the 'user_stories' key from one or more serialized milestone dicts."""
    for item in data if isinstance(data, list) else [data]:
        item.pop("user_stories", None)
    return data


@mcp.tool()
def list_milestones(
    project: str | int | None = None,
    filters: dict[str, Any] | None = None,
    include_user_stories: bool = True,
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
    strict_filters: bool = False,
) -> list[dict[str, Any]]:
    """List milestones (sprints), optionally scoped to a project.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.
    Each milestone embeds its full `user_stories`; pass `include_user_stories=False`
    to strip that (potentially large) field from every returned milestone.

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics. `strict_filters=True` raises instead of silently
    ignoring a `filters` key that collides with this tool's own parameter names.
    """
    _check_strict_filters(filters, strict_filters)
    query = dict(filters or {})
    if project is not None:
        query["project"] = _resolve_project_id(project)
    result = to_jsonable(get_client().milestones.list(**_paginated(query)))
    if not include_user_stories:
        result = _strip_user_stories(result)
    return apply_payload(result, "milestone", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


@mcp.tool()
def get_milestone(
    id: int,  # noqa: A002
    include_user_stories: bool = True,
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
) -> dict[str, Any]:
    """Get a milestone by id.

    The milestone embeds its full `user_stories`; pass `include_user_stories=False`
    to strip that (potentially large) field from the returned milestone.

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics.
    """
    result = to_jsonable(get_client().milestones.get(id))
    if not include_user_stories:
        result = _strip_user_stories(result)
    return apply_payload(result, "milestone", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


@mcp.tool()
def create_milestone(
    project: str | int,
    name: str,
    estimated_start: str,
    estimated_finish: str,
    fields: dict[str, Any] | None = None,
    return_representation: Literal["full", "minimal", "none"] = "full",
) -> dict[str, Any]:
    """Create a milestone. Dates are ISO strings ('YYYY-MM-DD').

    `return_representation` ("full" default / "minimal" / "none") controls how much of the
    created resource comes back - see docs/mcp.rst.
    """
    pid = _resolve_project_id(project)
    resource = get_client().milestones.create(pid, name, estimated_start, estimated_finish, **(fields or {}))
    if return_representation == "full":
        return to_jsonable(resource)
    return _represent(resource, fields or {}, return_representation)


@mcp.tool()
def delete_milestone(id: int) -> dict[str, str]:  # noqa: A002
    """Delete a milestone by id."""
    get_client().milestones.delete(id)
    return {"status": "deleted", "id": str(id)}


# --- Wiki pages -----------------------------------------------------------------------------


@mcp.tool()
def list_wiki_pages(
    project: str | int | None = None,
    filters: dict[str, Any] | None = None,
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
    strict_filters: bool = False,
) -> list[dict[str, Any]]:
    """List wiki pages, optionally scoped to a project.

    Paginated: defaults to page 1 of up to 100 results. Pass `filters` with `page`/
    `page_size` to page further, or `order_by` (e.g. '-created_date') to control order.

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics. `strict_filters=True` raises instead of silently
    ignoring a `filters` key that collides with this tool's own parameter names.
    """
    _check_strict_filters(filters, strict_filters)
    query = dict(filters or {})
    if project is not None:
        query["project"] = _resolve_project_id(project)
    result = to_jsonable(get_client().wikipages.list(**_paginated(query)))
    return apply_payload(result, "wikipage", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


@mcp.tool()
def get_wiki_page(
    id: int,  # noqa: A002
    payload: Literal["full", "compact", "minimal"] = "full",
    fields: list[str] | None = None,
    strip_media: bool | None = None,
    expand: list[str] | None = None,
) -> dict[str, Any]:
    """Get a wiki page by id.

    `payload`/`fields`/`strip_media`/`expand` optionally shrink the response - see
    docs/mcp.rst for full semantics.
    """
    result = to_jsonable(get_client().wikipages.get(id))
    return apply_payload(result, "wikipage", payload=payload, fields=fields, strip_media=strip_media, expand=expand)


@mcp.tool()
def create_wiki_page(
    project: str | int,
    slug: str,
    content: str,
    fields: dict[str, Any] | None = None,
    return_representation: Literal["full", "minimal", "none"] = "full",
) -> dict[str, Any]:
    """Create a wiki page.

    `return_representation` ("full" default / "minimal" / "none") controls how much of the
    created resource comes back - see docs/mcp.rst. Wiki pages have no `ref` number, so
    "minimal"/"none" here never include a `ref` key.
    """
    pid = _resolve_project_id(project)
    resource = get_client().wikipages.create(pid, slug, content, **(fields or {}))
    if return_representation == "full":
        return to_jsonable(resource)
    return _represent(resource, fields or {}, return_representation)


@mcp.tool()
def update_wiki_page(
    id: int,  # noqa: A002
    fields: dict[str, Any],
    return_representation: Literal["full", "minimal", "none"] = "full",
) -> dict[str, Any]:
    """Update a wiki page. `fields` is a dict of the attributes to change.

    `return_representation` ("full" default / "minimal" / "none") - see `update_user_story`
    for the full explanation; "minimal"/"none" skip the re-fetch this tool otherwise performs.
    Wiki pages have no `ref` number, so "minimal"/"none" here never include a `ref` key.
    """
    # See update_user_story: patch() doesn't refresh the local object, so re-fetch it for "full".
    client = get_client()
    resource = client.wikipages.get(id)
    _patch(resource, fields)
    if return_representation == "full":
        return to_jsonable(client.wikipages.get(id))
    return _represent(resource, fields, return_representation)
