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
    uvx --from "python-taiga[mcp]" taiga-mcp-server   # no persistent install at all

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
    taiga-mcp-server

The server speaks MCP over stdio and is meant to be launched by an MCP
client, not used interactively - the command above will sit and wait for a
client to connect over stdin/stdout.

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
      -- taiga-mcp-server

``--scope user`` stores the registration in your own Claude configuration,
not in any particular project. Check it went through with:

.. code:: shell

    claude mcp get taiga

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

``add_comment``
    Add a comment to a user story, task, issue or epic.

``get_history``
    Get the full change/comment history of a user story, task, issue, epic or
    wiki page. Each entry's `comment` field is empty for plain field-change
    events and non-empty for an actual comment; `delete_comment_date` is
    non-null if that comment was later deleted.

``list_user_stories``, ``get_user_story``, ``create_user_story``, ``update_user_story``, ``delete_user_story``
    Manage user stories.

``list_tasks``, ``get_task``, ``create_task``, ``update_task``, ``delete_task``
    Manage tasks, optionally scoped to a project and/or a user story.

``list_issues``, ``get_issue``, ``create_issue``, ``update_issue``, ``delete_issue``
    Manage issues.

``list_epics``, ``get_epic``, ``create_epic``, ``update_epic``, ``delete_epic``
    Manage epics.

``list_milestones``, ``get_milestone``, ``create_milestone``, ``delete_milestone``
    Manage milestones (sprints).

``list_wiki_pages``, ``get_wiki_page``, ``create_wiki_page``, ``update_wiki_page``
    Manage wiki pages.

.. tip:: Call ``get_project`` first when creating or updating an entity - it
         returns every status/priority/severity/points id valid for that
         project, which the ``create_*``/``update_*`` tools expect.

.. tip:: Every ``list_*`` tool is paginated and defaults to page 1 of up to
         100 results. Pass ``page``/``page_size`` in ``filters`` to move
         through further pages, and ``order_by`` (e.g. ``-created_date``) to
         control ordering - for example to fetch the most recent items first.

****************
Security notes
****************

The MCP server has the same permissions as the account it authenticates
with, and the create/update/delete tools above are destructive: an assistant
with access to this server can create, modify or delete real data in your
Taiga projects. Review what an MCP client proposes to do before approving
write operations, and consider a dedicated Taiga account with restricted
project membership if you want to limit the blast radius.
