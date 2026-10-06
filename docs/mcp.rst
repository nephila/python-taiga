.. :mcp:

==========
MCP Server
==========

Contents:

python-taiga ships a `Model Context Protocol <https://modelcontextprotocol.io/>`_
(MCP) server that exposes Taiga projects, user stories, tasks, issues, epics,
milestones and wiki pages as tools an LLM-based assistant (Claude, or any
other MCP-compatible client) can call directly, without you writing any glue
code.

.. note:: The MCP server wraps the same ``TaigaAPI`` documented in
          :doc:`the usage guide <usage>` and :doc:`the API reference <api>` -
          if you need to script against Taiga from Python yourself, use
          ``TaigaAPI`` directly instead.

****************
Installation
****************

The server is an optional extra, since it pulls in the official `MCP Python SDK
<https://github.com/modelcontextprotocol/python-sdk>`_ (``mcp``) as a dependency:

.. code:: shell

    pip install "python-taiga[mcp]"

Any of the following also work, depending on your toolchain:

.. code:: shell

    pip install --user "python-taiga[mcp]"   # no virtualenv management needed
    pipx install "python-taiga[mcp]"         # isolated venv, one command on PATH
    uvx --from "python-taiga[mcp]" taiga-mcp-server --help   # no persistent install at all

Any of these makes a ``taiga-mcp-server`` console script available.

****************
Configuration
****************

Credentials are read from environment variables, or from equivalent
command-line flags (flags take precedence over the environment):

.. list-table::
   :header-rows: 1
   :widths: 20 25 55

   * - Environment variable
     - CLI flag
     - Meaning
   * - ``TAIGA_HOST``
     - ``--host``
     - Taiga instance root, e.g. ``https://taiga.example.com``. Defaults to
       ``https://api.taiga.io``.
   * - ``TAIGA_TOKEN``
     - ``--token``
     - A pre-issued auth token. Takes precedence over username/password if
       both are set.
   * - ``TAIGA_TOKEN_TYPE``
     - ``--token-type``
     - Type of the token above. Defaults to ``Bearer``.
   * - ``TAIGA_USERNAME``
     - ``--username``
     - Username, used together with the password below.
   * - ``TAIGA_PASSWORD``
     - ``--password``
     - Password, exchanged for a session token at startup.
   * - ``TAIGA_TLS_VERIFY``
     - ``--tls-verify`` / ``--no-tls-verify``
     - Verify TLS certificates. Defaults to ``true``.

.. warning:: Prefer the environment variables over the CLI flags for
             ``--token``/``--password``: command-line arguments are visible
             to other processes on the same machine (e.g. via ``ps``),
             environment variables set for the server's own process are not.

.. note:: Most Taiga instances don't offer a durable personal-access-token
          feature - the token obtained from a username/password login is a
          short-lived JWT (often expiring within a day), and this server
          doesn't refresh it once started. Unless you know your instance
          issues long-lived tokens, configure ``TAIGA_USERNAME``/
          ``TAIGA_PASSWORD`` rather than a fixed ``TAIGA_TOKEN`` - the server
          re-authenticates fresh every time it starts.

******************************
Running the server standalone
******************************

.. code:: shell

    TAIGA_HOST=https://taiga.example.com \
    TAIGA_USERNAME=myuser \
    TAIGA_PASSWORD=mypassword \
    taiga-mcp-server serve

The server speaks MCP over stdio and is meant to be launched by an MCP
client, not used interactively - the command above will sit and wait for a
client to connect over stdin/stdout.

**********************************
Listing and calling tools directly
**********************************

Outside of an MCP client, ``taiga-mcp-server`` also exposes its tool set
directly from a shell:

.. code:: shell

    # list every tool, one per line
    taiga-mcp-server list-tools

    # ...with each tool's JSON input schema
    taiga-mcp-server list-tools --verbose

    # call a single tool by name, passing its arguments as a JSON object
    TAIGA_HOST=https://taiga.example.com \
    TAIGA_USERNAME=myuser \
    TAIGA_PASSWORD=mypassword \
    taiga-mcp-server call whoami --json '{}'

    taiga-mcp-server call get_project --json '{"project": "myproject"}'

On success, ``call`` prints the tool's JSON result to stdout. On failure
(unknown tool name, invalid arguments, or an error from the underlying
Taiga API call) it prints a message to stderr and exits with a non-zero
status.

*****************************
Connecting an MCP client
*****************************

Any MCP client that supports the stdio transport can launch
``taiga-mcp-server`` as a subprocess. For `Claude Code
<https://docs.claude.com/en/docs/claude-code>`_, register it once and it's
available in every project:

.. code:: shell

    claude mcp add --scope user taiga \
      -e TAIGA_HOST=https://taiga.example.com \
      -e TAIGA_USERNAME=myuser \
      -e TAIGA_PASSWORD=mypassword \
      -- "$(command -v taiga-mcp-server)" serve

``--scope user`` stores the registration in your own Claude configuration,
not in any particular project. Check it went through with:

.. code:: shell

    claude mcp get taiga

.. warning:: **Some MCP clients require every declared parameter to be passed
             explicitly, even ones with a documented default.** Every
             parameter below that shows a default (e.g. ``payload="full"``,
             ``strict_filters=False``) is genuinely optional in this server's
             own JSON schema and its runtime validation - confirmed by
             calling the real server directly over the MCP protocol,
             omitting those parameters entirely. Some MCP clients have
             nonetheless been observed rejecting the call outright
             (``-32602``, wording resembling Zod's ``nonoptional`` schema
             check) when a parameter carrying a schema-level ``default`` is
             omitted - for *every* such parameter, not just the ones this
             server added recently: `include_user_stories` on
             ``list_milestones`` (which predates this server's payload-
             reduction work) triggers the same rejection on an affected
             client. This is a property of that client's own schema
             validation, not of this server, and there is no available hook
             in this server's dependencies to change what gets emitted to
             work around it. **If your client exhibits this, pass every
             parameter explicitly on every call to an affected tool** -
             there is no way to make a client-side check like this
             optional from the server side.

****************
Available tools
****************

``whoami``
    Return the Taiga user currently authenticated.

``list_projects`` / ``get_project``
    List projects visible to the user, or fetch one project's full detail
    (numeric id or slug) - including the statuses/priorities/severities/points
    ids needed to create or update entities in it.

``search``
    Search user stories, tasks, issues, epics and wiki pages in a project.

``list_memberships``
    List a project's memberships (username, full_name, user_email, role_name,
    etc.) - the pool of users assignable as owner/assigned_to/watcher on that
    project's items.

``add_comment`` / ``add_comment_by_id``
    Add a comment to a user story, task, issue or epic, identified by
    ``project`` + ``ref`` (primary) or by database ``id`` (secondary, see
    below).

``get_history`` / ``get_history_by_id``
    Get the full change/comment history of a user story, task, issue, epic or
    wiki page. Each entry's `comment` field is empty for plain field-change
    events and non-empty for an actual comment; `delete_comment_date` is
    non-null if that comment was later deleted. Wiki pages have no ref number
    in Taiga, so for ``entity_type="wiki"`` pass the page's database id as
    ``ref`` and omit ``project``.

``get_custom_attributes_values`` / ``get_custom_attributes_values_by_id``
    Get the custom-attribute values of a user story, task, issue or epic.
    Keys of ``attributes_values`` are attribute ids as strings - see
    ``get_project``'s ``*_custom_attributes`` lists for id -> name.

``set_custom_attribute_value`` / ``set_custom_attribute_value_by_id``
    Set one custom-attribute value on a user story, task, issue or epic.
    ``attribute_id`` is the numeric id from ``get_project``'s
    ``*_custom_attributes`` list.

.. important:: The ``version`` returned by ``get_custom_attributes_values``
         (and expected by ``set_custom_attribute_value``) belongs to that
         custom-attributes-values resource - a separate version sequence
         from the entity's own ``version`` field. ``version`` is optional
         on ``set_custom_attribute_value``: when omitted, the resource's
         current version is used. If you pass one, it must come from a
         prior ``get_custom_attributes_values`` call, not the entity's own
         ``version``.

``list_user_stories``, ``get_user_story``, ``create_user_story``, ``update_user_story``, ``delete_user_story``
    Manage user stories.

``list_tasks``, ``get_task``, ``create_task``, ``update_task``, ``delete_task``
    Manage tasks, optionally scoped to a project and/or a user story.

``list_issues``, ``get_issue``, ``create_issue``, ``update_issue``, ``delete_issue``
    Manage issues.

``list_epics``, ``get_epic``, ``create_epic``, ``update_epic``, ``delete_epic``
    Manage epics.

``link_epic_user_story`` / ``link_epic_user_story_by_id``
    Link a user story to an epic, identifying both by their per-project ref
    numbers (primary) or by database id (secondary, see below).

``update_work_items``
    Update a batch of user stories/tasks/issues/epics in one call - see the
    tip below for the exact shape and its non-atomic semantics.

.. important:: ``get_user_story``/``get_task``/``get_issue``/``get_epic`` and
         their ``update_*``/``delete_*`` counterparts take a ``project`` (id
         or slug) and a ``ref`` - the per-project sequential number Taiga
         shows in its UI and URLs (e.g. the ``45634`` in
         ``.../issues/45634``). That ref is **not** the database id used
         internally for updates/deletes - it's only unique within a project,
         so it must be resolved together with ``project``. This is the
         primary, recommended way to address an entity, since numbers a user
         pastes from a Taiga URL or mentions in conversation are almost
         always refs.

         Each of these tools also has a ``_by_id`` counterpart (e.g.
         ``get_issue_by_id``, ``update_task_by_id``, ``delete_epic_by_id``,
         ``add_comment_by_id``) that takes the raw database ``id`` instead.
         These are a secondary, non-default lookup path - use them only when
         you already hold the database id (for example from a prior tool
         response), not a ref.

``list_milestones``, ``get_milestone``
    List/get milestones (sprints), optionally scoped to a project (``list_milestones``
    only). Each milestone embeds its full ``user_stories`` - pass
    ``include_user_stories=False`` to strip that (potentially large) field from the
    result. This embedded route is the cheapest way to get every story in a sprint in
    one call (pair it with ``fields=["id", "user_stories.ref", ...]`` to shrink it
    further), but Taiga's embedded story serializer carries only the single primary
    ``assigned_to`` - it has no ``assigned_users`` key at all, so multi-assignee data is
    unavailable through this route regardless of ``fields``/``resolve_assigned_users``.
    For complete multi-assignee data, fetch those stories individually with
    ``list_user_stories``/``get_user_story`` instead.

``create_milestone``, ``delete_milestone``
    Create/delete milestones (sprints).

``list_wiki_pages``, ``get_wiki_page``, ``create_wiki_page``, ``update_wiki_page``
    Manage wiki pages, optionally scoped to a project.

.. tip:: Call ``get_project`` first when creating or updating an entity - it
         returns every status/priority/severity/points id valid for that
         project, which the ``create_*``/``update_*`` tools expect.

.. tip:: Every ``list_*`` tool is paginated and defaults to page 1 of up to
         100 results. Pass ``page``/``page_size`` in ``filters`` to move
         through further pages, and ``order_by`` (e.g. ``-created_date``) to
         control ordering - for example to fetch the most recent items first.

.. tip:: Every ``list_*``/``get_*`` tool that returns a full resource - projects,
         user stories, tasks, issues, epics, milestones, memberships, wiki pages -
         accepts four further parameters to shrink an oversized response, all
         opt-in (the default reproduces today's full response exactly):

         - ``payload``: ``"full"`` (default, untouched) / ``"compact"`` (drops
           avatar/logo URLs and shrinks every ``*_extra_info`` block to its id
           plus display name) / ``"minimal"`` (only the fields a sprint-planning
           report actually reads - currently defined for user stories, issues,
           epics and milestones; for any other resource ``"minimal"`` behaves
           the same as ``"compact"`` for now). The exact field set kept by
           ``payload="minimal"`` per entity (``MINIMAL_FIELDS`` in
           ``taiga/mcp_server/serialize.py``):

           - ``milestone`` (``list_milestones``/``get_milestone``): ``id``,
             ``name``, ``slug``, ``project``, ``project_extra_info.name``,
             ``project_extra_info.slug``, ``estimated_start``,
             ``estimated_finish``, ``closed``. The board's name/slug are
             included alongside the bare ``project`` id specifically so a
             cross-project report can display and link each board without a
             second call.
           - ``userstory`` (``list_user_stories``/``get_user_story``/
             ``get_user_story_by_id``): ``id``, ``ref``, ``subject``,
             ``version``, ``milestone``, ``milestone_name``,
             ``status_extra_info.name``, ``status_extra_info.is_closed``,
             ``is_closed``, ``finish_date``, ``is_blocked``,
             ``assigned_to_extra_info.full_name_display``,
             ``assigned_users``, ``epics.ref``, ``assigned_users_extra_info``.
             The numeric ``status`` id is deliberately omitted - it is a
             per-project id, not comparable across boards, and redundant
             alongside ``status_extra_info.name``. ``assigned_users`` (the
             bare secondary-assignee id list) is included so ``minimal``
             never silently under-reports who is assigned; pair it with
             ``resolve_assigned_users=True`` for names, not just ids.
           - ``issue`` (``list_issues``/``get_issue``/``get_issue_by_id``):
             same as ``userstory`` minus ``assigned_users``/
             ``assigned_users_extra_info`` (issues have no ``assigned_users``).
           - ``epic`` (``list_epics``/``get_epic``/``get_epic_by_id``):
             ``id``, ``ref``, ``subject``, ``status_extra_info.name``,
             ``project``.
         - ``fields``: an explicit list of field paths, overriding ``payload``
           entirely, e.g. ``["ref", "subject", "status_extra_info.name"]``. A
           dotted path keeps only that nested key; if the value at that point is
           itself a list (e.g. a story's ``epics``), the remaining path is
           applied to every element, e.g. ``"epics.ref"``.
         - ``strip_media``: ``True``/``False``, overriding whether avatar/logo
           URLs (``photo``, ``big_photo``, ``gravatar_id``, ``logo_small_url``)
           are stripped, regardless of ``payload``. These carry rotating
           signed-URL signatures, so leaving them in also defeats prompt caching
           between otherwise-identical calls.
         - ``expand``: a list of top-level block names to add back at full
           detail on top of a reduced ``payload``, e.g.
           ``payload="minimal", expand=["assigned_to_extra_info"]``.

         ``list_user_stories``, ``get_user_story`` and ``get_user_story_by_id``
         additionally accept ``resolve_assigned_users=True``: ``assigned_users``
         is a bare list of user ids with no names anywhere in the default
         payload, so this resolves them into
         ``assigned_users_extra_info: [{"id", "full_name_display"}, ...]`` via
         that story's project memberships. Off by default because, unlike the
         four parameters above, it adds a request rather than removing one (one
         ``list_memberships`` call per distinct project touched).

         Every ``list_*`` tool additionally accepts ``strict_filters=False``
         (default): pass ``True`` to raise immediately if ``filters`` nests one
         of this server's own parameter names by mistake (e.g.
         ``filters={"include_user_stories": False}``) instead of silently
         returning an unfiltered response - Taiga's REST backend ignores
         unknown query parameters with no error either way, which measured as
         much as a 24x size regression with no signal that anything went wrong.

         **`strict_filters` is a narrow guard, not a filter validator.** It
         only catches this server's own parameter names appearing inside
         `filters` by mistake. It gives **no protection** against a
         misspelled or unsupported Taiga filter key (e.g. `milestone__in`,
         which Taiga silently ignores rather than erroring - see the note
         below) - that class of mistake returns a normal-looking but wrong
         result set with no error either way, `strict_filters` or not. Any
         filter-based narrowing this server accepts must be re-asserted
         client-side (e.g. checking the returned items' own fields match
         what the filter was supposed to select) rather than trusted purely
         because the call didn't raise.

.. note:: ``filters`` is forwarded as-is to Taiga's REST endpoint, so
          server-side filtering - e.g. ``list_milestones(filters={"closed":
          False, "estimated_start__lte": "2026-09-20"})`` - already works
          today with no MCP-side change, for any lookup Taiga's own API
          filter backend supports. Which lookups that includes is a property
          of the Taiga server you're talking to, not of this client. Filters
          verified against a live instance: ``closed`` (milestones),
          ``page_size`` (all ``list_*`` tools, caps at 100 per page regardless
          of the value requested), ``estimated_start__lte``/
          ``estimated_finish__gte`` (milestones - returns exactly the boards
          whose window overlaps the given range), and ``milestone`` as a
          single int (user stories, issues). A comma-separated list of ids is
          **not** supported the same way for either ``milestone`` (errors) or
          ``milestone__in`` (silently ignored, returning an arbitrary unrelated
          page of results rather than an error) - do not rely on either form;
          fetch each milestone's items with its own call instead. A Python
          *list* value (e.g. ``filters={"milestone": [1444, 1446]}``) is a
          third failure mode, and the most dangerous of the three: it returns
          a small, clean, plausible-looking result set - but only for the
          *last* id in the list, with every other id's items silently
          dropped. This client sends the list correctly (as repeated query
          parameters, standard ``requests`` behaviour); the collapse happens
          in Taiga's own REST backend, which appears to read only the last
          value of a repeated parameter (standard Django ``QueryDict.get()``
          semantics) - nothing on this client's side can change that. Do not
          pass a list as a filter value for any key; fetch each id with its
          own call instead. Separately,
          ``project=None`` (the default on item-listing tools) already returns
          results across every project the caller can see - no project scope
          is required for a cross-project item query.

.. note:: Taiga's own data can disagree with itself on closure state: the
          top-level ``is_closed`` field and ``status_extra_info.is_closed``
          are two independently-set signals and have been observed to
          contradict each other on the same item (e.g. ``is_closed: true``
          while the status is actually "In progress" and
          ``status_extra_info.is_closed: false``). This is a property of the
          underlying Taiga data, not a serialization defect in this server.
          ``status_extra_info.name``/``status_extra_info.is_closed`` are the
          more reliable signals if the two disagree - they come directly from
          the status Taiga's UI itself displays, rather than a separately
          maintained flag on the item.

.. tip:: Every ``create_*``/``update_*`` tool accepts ``return_representation``
         (``"full"`` default / ``"minimal"`` / ``"none"``), opt-in, to shrink
         what a write echoes back:

         - ``"full"`` (default): the complete written resource, exactly as
           before.
         - ``"minimal"``: ``{"id", "ref" (only if the entity has one),
           "version", ...the fields you passed in ``fields``}`` - never the
           tool's own required arguments (``subject``, ``status``, etc.),
           since you already know those - only ``id``/``ref``/``version`` are
           genuinely new information a write produces.
         - ``"none"``: ``{"ok": true, "id", "ref" (if any), "version"}`` - a
           bare acknowledgement.

         On ``update_*`` tools, ``"minimal"``/``"none"`` also skip the
         re-fetch these tools otherwise perform after writing - a latency
         win, not just a smaller response. ``version`` is not a separate
         parameter on any ``create_*``/``update_*`` tool: if ``fields`` has no
         ``version``, the tool uses the current version of the item it has
         just fetched for optimistic locking; an explicit ``version`` inside
         ``fields`` wins. (``set_custom_attribute_value``/``set_custom_attribute_value_by_id``
         take their own optional ``version`` - see the note above on that
         unrelated ``version`` sequence.)

.. tip:: ``update_work_items(project, updates, return_representation="full")``
         updates a batch of user stories/tasks/issues/epics in one call.
         Each entry in ``updates`` is
         ``{"entity_type": "user_story"|"task"|"issue"|"epic", "ref": <int>,
         "fields": {...}}``. **Not atomic** - items are processed in order,
         each succeeds or fails independently, and one failure never rolls
         back or blocks any other item. Returns one result row per input
         item, in the same order (zip ``updates`` with the result to match
         them up); a failed item's row is
         ``{"status": "error", "entity_type", "ref", "error"}``. If the write
         succeeded but the follow-up re-fetch needed for
         ``return_representation`` failed, the row is instead
         ``{"status": "updated", "entity_type", "ref", "id",
         "readback_error"}`` - the change **was applied**, so don't retry it;
         re-read the item to see its current state. Wiki pages
         aren't supported here (no per-project ``ref``) - use
         ``update_wiki_page`` directly.
         As with the single-item tools, a missing ``version`` in an item's
         ``fields`` is filled in from the item just fetched.

****************
Security notes
****************

The MCP server has the same permissions as the account it authenticates
with, and the create/update/delete tools above are destructive: an assistant
with access to this server can create, modify or delete real data in your
Taiga projects. Review what an MCP client proposes to do before approving
write operations, and consider a dedicated Taiga account with restricted
project membership if you want to limit the blast radius.

``set_custom_attribute_value``/``set_custom_attribute_value_by_id`` and
``link_epic_user_story``/``link_epic_user_story_by_id`` are also writes and
fall under the same destructive-tools framing above.
