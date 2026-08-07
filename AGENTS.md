# Agent instructions

This file gives coding agents (Claude Code and similar) step-by-step
instructions for tasks specific to this repository. Human-facing docs live in
``README.rst`` and ``docs/``.

## Registering the Taiga MCP server in the user's global Claude config

This repo ships an MCP server (`taiga/mcp_server/`) that exposes the Taiga
REST API as tools over stdio, via the `taiga-mcp-server` console script
(installed by the `mcp` extra: `pip install -e .[mcp]` from this repo, or
`pip install python-taiga[mcp]` from PyPI).

When asked to "add the Taiga MCP server to Claude" / "register taiga-mcp
globally" / "add it to my user-wide config", follow this procedure:

1. **Confirm before acting.** Registering at user scope changes the user's
   global Claude Code config (`~/.claude.json`), applying to every project,
   not just this repo. Confirm the target Taiga instance and scope with the
   user before running the command, unless they've already given explicit
   go-ahead in this conversation.

2. **Get a stable `taiga-mcp-server` binary.** Don't point the MCP config at
   a project-local `.venv` — Claude Code launches MCP server commands without
   inheriting an activated venv, and the binary disappears if that venv is
   ever recreated. Install it somewhere durable instead. There are several
   equally valid ways to do this; pick whichever fits the user's toolchain,
   asking if it's unclear, and default to `pip install --user` since it needs
   nothing beyond a reasonably modern Python:
   ```bash
   # default: pip install --user (works with any modern Python/pip)
   pip install --user "python-taiga[mcp]"          # from PyPI
   pip install --user -e ".[mcp]"                  # from this checkout

   # pipx (isolated venv per tool, one binary on PATH)
   pipx install "python-taiga[mcp]"                # from PyPI
   pipx install --editable ".[mcp]"                # from this checkout

   # uvx (no persistent install; uv manages an ephemeral/cached env)
   # here the *registered command* becomes `uvx --from "python-taiga[mcp]" taiga-mcp-server`
   # instead of a resolved path — see the uvx example in step 4.
   ```
   After a `pip --user`/`pipx` install, resolve the resulting path and use it
   verbatim in step 4:
   ```bash
   command -v taiga-mcp-server
   ```

3. **Collect credentials.** Ask the user for:
   - `TAIGA_HOST` — the Taiga site root, e.g. `https://taiga.nephila.it`.
     For self-hosted instances this is *not* an `api.` subdomain and has no
     `/api` suffix — the client appends `/api/v1` itself.
   - Either `TAIGA_TOKEN` (pre-issued API token), or both
     `TAIGA_USERNAME` and `TAIGA_PASSWORD`. A token takes precedence if both
     are configured.
   - Optional: `TAIGA_TOKEN_TYPE` (default `Bearer`), `TAIGA_TLS_VERIFY`
     (default `true`).

   Never pass `--token`/`--password` as CLI arguments — they'd be visible in
   the process list. Always pass credentials as environment variables.

4. **Register at user scope** with `claude mcp add`, using `-e` for every
   credential env var and the resolved binary (or `uvx` invocation) from
   step 2:
   ```bash
   claude mcp add --scope user taiga \
     -e TAIGA_HOST=https://taiga.nephila.it \
     -e TAIGA_USERNAME=<username> \
     -e TAIGA_PASSWORD=<password> \
     -- /absolute/path/to/taiga-mcp-server
   ```
   or, with a token instead of username/password:
   ```bash
   claude mcp add --scope user taiga \
     -e TAIGA_HOST=https://taiga.nephila.it \
     -e TAIGA_TOKEN=<token> \
     -- /absolute/path/to/taiga-mcp-server
   ```
   With `uvx` there's no path to resolve — pass the `uvx` invocation itself
   as the command:
   ```bash
   claude mcp add --scope user taiga \
     -e TAIGA_HOST=https://taiga.nephila.it \
     -e TAIGA_TOKEN=<token> \
     -- uvx --from "python-taiga[mcp]" taiga-mcp-server
   ```
   `--scope user` (not `local`/`project`) is what makes it "user-wide" —
   available in every project for that user, stored outside this repo.

5. **Verify** with `claude mcp list` (look for `taiga` ... `✔ Connected`) and
   `claude mcp get taiga`. If it fails to connect, re-check the resolved
   binary/command from step 2 and that `TAIGA_HOST` is the site root, not an
   API subdomain.

6. **Don't persist secrets in the repo.** Credentials belong only in the
   `claude mcp add -e ...` invocation (stored in the user's own
   `~/.claude.json`) — never write them into files inside this repository.
