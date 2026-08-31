# Taiga MCP CLI Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give `taiga-mcp-server` the same CLI verb shape as `ring-mcp-server` — `serve`, `list-tools [--verbose]`, `call <tool_name> --json '<json>'` — without touching any of the ~45 hand-implemented `@mcp.tool()` functions in `taiga/mcp_server/server.py`.

**Architecture:** Rewrite `taiga/mcp_server/cli.py` from `argparse` to `typer`. `serve` preserves today's behavior byte-for-byte, now behind an explicit subcommand instead of the bare invocation. `list-tools` and `call` invoke the already-constructed `mcp` object in-process via `asyncio.run(mcp.list_tools())` / `asyncio.run(mcp.call_tool(name, arguments))` — no subprocess, no live MCP client round trip.

**Tech Stack:** Python 3.11–3.14, `typer` (new dependency, `>=0.12.0` to match `ring-mcp-server`'s own floor), `mcp==2.0.0` (already pinned via the `[mcp]` extra), `pytest` + `typer.testing.CliRunner`.

**Spec:** `artifacts/specs/2026-08-31-mcp-cli-parity-design.md`

## Global Constraints

- Do not modify `taiga/mcp_server/server.py`, `taiga/mcp_server/auth.py`, or `taiga/mcp_server/serialize.py` — tool bodies, credential resolution, and serialization stay exactly as they are (spec §Non-goals).
- Do not rename any of the ~45 existing tool functions or their parameters (spec §Non-goals).
- `serve`'s auth flags/env-var precedence (flag > env > default) must remain identical to today's argparse behavior (spec §1).
- Console script stays `taiga-mcp-server = taiga.mcp_server.cli:main` in `setup.cfg` — no entry-point path change, `main()` just becomes a thin `app()` wrapper.
- Every new/changed behavior gets a test; no live Taiga server or network access in any test (spec §4).
- **Breaking change**: bare `taiga-mcp-server` (no subcommand) no longer starts the server. With Typer's `no_args_is_help=True` (same setting `ring-mcp-server`'s own CLI uses), it now prints the command list/help and exits 0 instead — this is a precision correction to the spec's "becomes a usage error" wording (see Task 6, which also amends the spec file itself for accuracy) — but it stops silently defaulting to `serve`, which is the compatibility break that matters.
- This branch (`feature/issue-14039-taiga-mcp-cli-parity`) is based on `feature/issue-267-add-mcp`. Do not rebase onto `master` as part of this plan — that happens later, once issue-267 merges (spec §Open items).

---

## File Structure

| File | Change |
|---|---|
| `taiga/mcp_server/cli.py` | Rewritten: argparse → Typer, 3 subcommands |
| `tests/test_mcp_server_cli.py` | Rewritten: `cli.main(argv)` calls → `CliRunner.invoke(cli.app, argv)` |
| `setup.cfg` | `[options.extras_require].mcp` gains `typer>=0.12.0` |
| `docs/mcp.rst` | Bare-invocation examples get ` serve`; new "Listing and calling tools directly" section |
| `AGENTS.md` | Two `claude mcp add ... -- taiga-mcp-server` examples get ` serve` |
| `changes/14039.feature` | New towncrier fragment |
| `changes/14039.removal` | New towncrier fragment (the breaking change) |
| `artifacts/specs/2026-08-31-mcp-cli-parity-design.md` | One-sentence precision amendment (Task 6) |

`_env_bool()` in `cli.py` is unchanged and reused as-is by the new `serve`/`list-tools`/`call` credential resolution — it has no Typer dependency, it's a pure env-var helper.

---

## Task 1: Add the Typer dependency

**Files:**
- Modify: `setup.cfg`

**Interfaces:**
- Produces: `typer` importable wherever the `[mcp]` extra is installed — every later task in this plan depends on this.

- [ ] **Step 1: Add the dependency**

In `setup.cfg`, under `[options.extras_require]`:

```ini
[options.extras_require]
docs =
	sphinx
    sphinx-rtd-theme
mcp =
    mcp~=2.0
    typer>=0.12.0
```

- [ ] **Step 2: Install it into the dev environment**

Run: `pip install -e ".[mcp]"`, or `tox -e py313 --recreate` to rebuild the existing `.tox/py313` env (which already has `mcp` installed per the design's own investigation) so it picks up the new `typer` dependency from `setup.cfg`.

- [ ] **Step 3: Verify the import works**

Run: `python -c "import typer; print(typer.__version__)"` (or the equivalent inside the relevant tox env) — expect a version string, no `ImportError`.

- [ ] **Step 4: Commit**

```bash
git add setup.cfg
git commit -m "build(mcp): add typer dependency for the taiga-mcp-server CLI"
```

---

## Task 2: Rewrite `cli.py`'s skeleton and `serve` subcommand

**Files:**
- Modify: `taiga/mcp_server/cli.py` (full rewrite)
- Test: `tests/test_mcp_server_cli.py` (rewrite the `main`-based tests; `_env_bool` tests are unchanged)

**Interfaces:**
- Consumes: `taiga.mcp_server.auth.{DEFAULT_HOST, DEFAULT_TOKEN_TYPE, Credentials, configure}` (all unchanged, from Task 1's untouched `auth.py`).
- Produces: `taiga.mcp_server.cli.app` (a `typer.Typer` instance — later tasks add commands to it), `taiga.mcp_server.cli.main() -> None` (console-script entry point), `taiga.mcp_server.cli._env_bool(name: str, default: bool) -> bool` (unchanged signature), `taiga.mcp_server.cli._resolve_credentials(host, token, token_type, username, password, tls_verify) -> Credentials` (new — later tasks reuse this for `list-tools` and `call`).

- [ ] **Step 1: Write the failing tests for `serve`**

Replace the `# --- main` section of `tests/test_mcp_server_cli.py` (keep the `_env_bool` tests above it untouched) with:

```python
from typer.testing import CliRunner

from taiga.mcp_server import cli

runner = CliRunner()

# --- serve ------------------------------------------------------------------------------


@patch("taiga.mcp_server.server.mcp")
@patch("taiga.mcp_server.cli.configure")
def test_serve_configures_from_token_argv(mock_configure, mock_mcp):
    result = runner.invoke(
        cli.app, ["serve", "--host", "https://example.com", "--token", "tok", "--no-tls-verify"]
    )

    assert result.exit_code == 0
    mock_configure.assert_called_once()
    credentials = mock_configure.call_args.args[0]
    assert credentials.host == "https://example.com"
    assert credentials.token == "tok"
    assert credentials.tls_verify is False
    mock_mcp.run.assert_called_once_with(transport="stdio")


@patch("taiga.mcp_server.server.mcp")
@patch("taiga.mcp_server.cli.configure")
def test_serve_configures_from_username_password_argv(mock_configure, mock_mcp):
    runner.invoke(cli.app, ["serve", "--username", "alice", "--password", "secret", "--tls-verify"])

    credentials = mock_configure.call_args.args[0]
    assert credentials.username == "alice"
    assert credentials.password == "secret"
    assert credentials.token is None
    assert credentials.tls_verify is True


@patch("taiga.mcp_server.server.mcp")
@patch("taiga.mcp_server.cli.configure")
def test_serve_reads_credentials_from_env(mock_configure, mock_mcp):
    env = {
        "TAIGA_HOST": "https://env.example.com",
        "TAIGA_TOKEN": "env-tok",
        "TAIGA_TOKEN_TYPE": "Basic",
    }
    with patch.dict("os.environ", env):
        result = runner.invoke(cli.app, ["serve"])

    assert result.exit_code == 0
    credentials = mock_configure.call_args.args[0]
    assert credentials.host == "https://env.example.com"
    assert credentials.token == "env-tok"
    assert credentials.token_type == "Basic"


@patch("taiga.mcp_server.server.mcp")
@patch("taiga.mcp_server.cli.configure")
def test_serve_falls_back_to_tls_verify_env_var(mock_configure, mock_mcp):
    with patch.dict("os.environ", {"TAIGA_TLS_VERIFY": "false"}):
        runner.invoke(cli.app, ["serve", "--token", "tok"])

    assert mock_configure.call_args.args[0].tls_verify is False


@patch("taiga.mcp_server.server.mcp")
@patch("taiga.mcp_server.cli.configure")
def test_serve_defaults_tls_verify_true_without_env_or_flag(mock_configure, mock_mcp):
    with patch.dict("os.environ", {}, clear=False):
        os.environ.pop("TAIGA_TLS_VERIFY", None)
        runner.invoke(cli.app, ["serve", "--token", "tok"])

    assert mock_configure.call_args.args[0].tls_verify is True


# --- bare invocation (breaking change) ---------------------------------------------------


@patch("taiga.mcp_server.server.mcp")
@patch("taiga.mcp_server.cli.configure")
def test_bare_invocation_no_longer_serves(mock_configure, mock_mcp):
    result = runner.invoke(cli.app, [])

    assert "serve" in result.output
    mock_configure.assert_not_called()
    mock_mcp.run.assert_not_called()
```

Delete the old `test_main_*` tests they replace (the argparse-specific ones: `test_main_configures_from_token_argv`, `test_main_configures_from_username_password_argv`, `test_main_reads_credentials_from_env`, `test_main_falls_back_to_tls_verify_env_var`, `test_main_defaults_tls_verify_true_without_env_or_flag`).

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_mcp_server_cli.py -v`
Expected: `ImportError`/`AttributeError` — `cli.app` doesn't exist yet (old `cli.py` is still argparse-based).

- [ ] **Step 3: Rewrite `cli.py`**

```python
# python-taiga
# Copyright 2015 Nephila
# See LICENSE for details.

from __future__ import annotations

import os
from typing import Optional

import typer

from .. import __version__
from .auth import DEFAULT_HOST, DEFAULT_TOKEN_TYPE, Credentials, configure

app = typer.Typer(add_completion=False, no_args_is_help=True, help="Taiga MCP server & CLI.")


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in ("0", "false", "no", "off")


def _resolve_credentials(
    host: Optional[str],
    token: Optional[str],
    token_type: Optional[str],
    username: Optional[str],
    password: Optional[str],
    tls_verify: Optional[bool],
) -> Credentials:
    return Credentials(
        host=host or os.environ.get("TAIGA_HOST", DEFAULT_HOST),
        tls_verify=_env_bool("TAIGA_TLS_VERIFY", True) if tls_verify is None else tls_verify,
        token=token or os.environ.get("TAIGA_TOKEN"),
        token_type=token_type or os.environ.get("TAIGA_TOKEN_TYPE", DEFAULT_TOKEN_TYPE),
        username=username or os.environ.get("TAIGA_USERNAME"),
        password=password or os.environ.get("TAIGA_PASSWORD"),
    )


HostOption = typer.Option(None, help="Taiga instance host (default: TAIGA_HOST env var, or https://api.taiga.io).")
TokenOption = typer.Option(None, help="Taiga auth token (default: TAIGA_TOKEN env var).")
TokenTypeOption = typer.Option(None, help="Type of the auth token (default: TAIGA_TOKEN_TYPE env var, or Bearer).")
UsernameOption = typer.Option(None, help="Taiga username (default: TAIGA_USERNAME env var).")
PasswordOption = typer.Option(None, help="Taiga password (default: TAIGA_PASSWORD env var).")
TlsVerifyOption = typer.Option(
    None,
    "--tls-verify/--no-tls-verify",
    help="Verify TLS certificates (default: TAIGA_TLS_VERIFY env var, or true).",
)


@app.command()
def serve(
    host: Optional[str] = HostOption,
    token: Optional[str] = TokenOption,
    token_type: Optional[str] = TokenTypeOption,
    username: Optional[str] = UsernameOption,
    password: Optional[str] = PasswordOption,
    tls_verify: Optional[bool] = TlsVerifyOption,
) -> None:
    """Run the MCP server over stdio.

    Credentials can be passed as flags or read from the TAIGA_HOST/TAIGA_TOKEN
    or TAIGA_HOST/TAIGA_USERNAME/TAIGA_PASSWORD environment variables. Passing
    --token/--password on the command line can expose them via the process
    list; prefer the environment variables where possible.
    """
    configure(_resolve_credentials(host, token, token_type, username, password, tls_verify))

    from .server import mcp

    mcp.run(transport="stdio")


def main() -> None:
    """Entry point for the ``taiga-mcp-server`` console script."""
    app()


if __name__ == "__main__":
    main()
```

Note: `--version` (previously `argparse`'s `action="version"`) is intentionally dropped from this step — Typer's idiom is a callback-based `--version` on the app itself, added in Task 3 alongside `list-tools` so it doesn't block this task's `serve`-only scope. If `--version` is needed sooner, it can be added here instead — not a hard dependency either way.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_mcp_server_cli.py -v`
Expected: PASS. (If `test_bare_invocation_no_longer_serves`'s exact exit code differs from what's asserted — the test above deliberately avoids asserting a specific exit code, only that `serve` wasn't triggered — no further action needed; if `"serve" in result.output` fails because Typer's help text formatting differs, inspect `result.output` and adjust the substring check, not the underlying behavior.)

- [ ] **Step 5: Commit**

```bash
git add taiga/mcp_server/cli.py tests/test_mcp_server_cli.py
git commit -m "feat(mcp)!: require explicit 'serve' subcommand for taiga-mcp-server

BREAKING CHANGE: bare 'taiga-mcp-server' with no subcommand no longer
starts the MCP server. Existing MCP client configs invoking the binary
with no arguments must add ' serve'."
```

---

## Task 3: Add `list-tools` subcommand

**Files:**
- Modify: `taiga/mcp_server/cli.py`
- Test: `tests/test_mcp_server_cli.py`

**Interfaces:**
- Consumes: `taiga.mcp_server.cli.{app, HostOption, TokenOption, TokenTypeOption, UsernameOption, PasswordOption, TlsVerifyOption, _resolve_credentials}` from Task 2; `taiga.mcp_server.server.mcp.list_tools() -> list[mcp_types.Tool]` (async, verified during design — see spec §2).
- Produces: `taiga-mcp-server list-tools [--verbose/-v]` subcommand.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_mcp_server_cli.py`:

```python
# --- list-tools ---------------------------------------------------------------------------


def test_list_tools_lists_all_tool_names():
    result = runner.invoke(cli.app, ["list-tools"])

    assert result.exit_code == 0
    assert "whoami" in result.output
    assert "list_user_stories" in result.output
    assert "create_issue" in result.output


def test_list_tools_default_excludes_schema():
    result = runner.invoke(cli.app, ["list-tools"])

    assert result.exit_code == 0
    assert '"properties"' not in result.output


def test_list_tools_verbose_includes_schema():
    result = runner.invoke(cli.app, ["list-tools", "--verbose"])

    assert result.exit_code == 0
    assert '"properties"' in result.output
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_mcp_server_cli.py -k list_tools -v`
Expected: FAIL — no `list-tools` command registered on `cli.app` yet (Typer/Click reports "No such command").

- [ ] **Step 3: Add the command**

In `taiga/mcp_server/cli.py`, add near the top:

```python
import asyncio
import json
```

(alongside the existing `import os`), and add the command itself after `serve`:

```python
@app.command("list-tools")
def list_tools(
    host: Optional[str] = HostOption,
    token: Optional[str] = TokenOption,
    token_type: Optional[str] = TokenTypeOption,
    username: Optional[str] = UsernameOption,
    password: Optional[str] = PasswordOption,
    tls_verify: Optional[bool] = TlsVerifyOption,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Include each tool's JSON input schema."),
) -> None:
    """List every tool exposed by the MCP server."""
    configure(_resolve_credentials(host, token, token_type, username, password, tls_verify))

    from .server import mcp

    tools = asyncio.run(mcp.list_tools())
    for tool in sorted(tools, key=lambda t: t.name):
        dumped = tool.model_dump(by_alias=True, exclude_none=True)
        typer.echo(f"{dumped['name']}\t{dumped.get('description', '')}")
        if verbose:
            typer.echo(json.dumps(dumped["inputSchema"], indent=2))
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_mcp_server_cli.py -k list_tools -v`
Expected: PASS.

- [ ] **Step 5: Run the full test file to check for regressions**

Run: `pytest tests/test_mcp_server_cli.py -v`
Expected: all PASS (Task 2's `serve` tests unaffected).

- [ ] **Step 6: Commit**

```bash
git add taiga/mcp_server/cli.py tests/test_mcp_server_cli.py
git commit -m "feat(mcp): add 'list-tools' subcommand to taiga-mcp-server"
```

---

## Task 4: Add `call` subcommand — success path

**Files:**
- Modify: `taiga/mcp_server/cli.py`
- Test: `tests/test_mcp_server_cli.py`

**Interfaces:**
- Consumes: `taiga.mcp_server.server.mcp.call_tool(name, arguments, context=None) -> CallToolResult` (async; `.structured_content` / `.content` fields — verified during design, spec §2–3).
- Produces: `taiga-mcp-server call <tool_name> --json/-j '<json>'` (happy path only — Task 5 adds the error matrix).

- [ ] **Step 1: Write the failing test**

Add to `tests/test_mcp_server_cli.py`:

```python
# --- call: success path --------------------------------------------------------------------


@patch("taiga.mcp_server.auth._client", None)
@patch("taiga.mcp_server.auth._credentials", None)
def test_call_success_prints_structured_json_result(monkeypatch):
    import taiga.mcp_server.server as server_mod

    monkeypatch.setattr(server_mod, "get_client", lambda: type("C", (), {"me": lambda self: {"id": 1, "username": "demo"}})())

    result = runner.invoke(cli.app, ["call", "whoami", "--json", "{}"])

    assert result.exit_code == 0
    assert json.loads(result.output) == {"id": 1, "username": "demo"}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_mcp_server_cli.py -k call_success -v`
Expected: FAIL — no `call` command registered yet.

- [ ] **Step 3: Add the command**

```python
@app.command()
def call(
    tool_name: str = typer.Argument(..., help="Tool name, as shown by list-tools."),
    arguments: str = typer.Option("{}", "--json", "-j", help="JSON object of arguments for the tool."),
    host: Optional[str] = HostOption,
    token: Optional[str] = TokenOption,
    token_type: Optional[str] = TokenTypeOption,
    username: Optional[str] = UsernameOption,
    password: Optional[str] = PasswordOption,
    tls_verify: Optional[bool] = TlsVerifyOption,
) -> None:
    """Call a single tool directly, bypassing an MCP client."""
    try:
        parsed_arguments = json.loads(arguments)
    except json.JSONDecodeError as exc:
        typer.echo(f"Invalid JSON in --json: {exc}", err=True)
        raise typer.Exit(1) from exc

    configure(_resolve_credentials(host, token, token_type, username, password, tls_verify))

    from .server import mcp

    result = asyncio.run(mcp.call_tool(tool_name, parsed_arguments))

    payload = result.structured_content if result.structured_content is not None else result.content
    typer.echo(json.dumps(payload, indent=2, default=str))
```

(No error handling yet — that's Task 5. This step only makes the success-path test pass.)

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_mcp_server_cli.py -k call_success -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add taiga/mcp_server/cli.py tests/test_mcp_server_cli.py
git commit -m "feat(mcp): add 'call' subcommand to taiga-mcp-server (success path)"
```

---

## Task 5: `call` subcommand — error matrix

**Files:**
- Modify: `taiga/mcp_server/cli.py`
- Test: `tests/test_mcp_server_cli.py`

**Interfaces:**
- Consumes: `mcp.server.mcpserver.exceptions.ToolError` (raised by `mcp.call_tool()` for unknown tool / validation failure / tool-internal exception, with `.__cause__` set to the underlying exception — verified live during design, spec §3); `mcp.shared.exceptions.MCPError` (unwrapped by the SDK, caught here defensively).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_mcp_server_cli.py`:

```python
# --- call: error matrix ---------------------------------------------------------------------


def test_call_invalid_json_errors():
    result = runner.invoke(cli.app, ["call", "whoami", "--json", "{not valid"])

    assert result.exit_code == 1
    assert "Invalid JSON in --json" in result.output


@patch("taiga.mcp_server.auth._client", None)
@patch("taiga.mcp_server.auth._credentials", None)
def test_call_unknown_tool_errors():
    result = runner.invoke(cli.app, ["call", "this_tool_does_not_exist", "--json", "{}"])

    assert result.exit_code == 1
    assert "Unknown tool: this_tool_does_not_exist" in result.output


@patch("taiga.mcp_server.auth._client", None)
@patch("taiga.mcp_server.auth._credentials", None)
def test_call_missing_required_argument_errors():
    result = runner.invoke(cli.app, ["call", "get_project", "--json", "{}"])

    assert result.exit_code == 1
    assert "Invalid arguments for get_project" in result.output


@patch("taiga.mcp_server.auth._client", None)
@patch("taiga.mcp_server.auth._credentials", None)
def test_call_tool_internal_exception_errors(monkeypatch):
    for var in ("TAIGA_TOKEN", "TAIGA_USERNAME", "TAIGA_PASSWORD"):
        monkeypatch.delenv(var, raising=False)

    result = runner.invoke(cli.app, ["call", "whoami", "--json", "{}"])

    assert result.exit_code == 1
    assert "Error calling whoami" in result.output
    assert "credentials" in result.output
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_mcp_server_cli.py -k "call_invalid_json or call_unknown_tool or call_missing_required or call_tool_internal" -v`
Expected: FAIL — `ToolError` currently propagates unhandled out of `call()`, causing `CliRunner` to report a non-zero exit but without the expected stderr message (Click captures the exception; `result.output` won't contain the intended text).

- [ ] **Step 3: Add error handling**

Add the import at the top of `cli.py`:

```python
from mcp.server.mcpserver.exceptions import ToolError
from mcp.shared.exceptions import MCPError
from pydantic_core import ValidationError as PydanticValidationError
```

Wrap the `call_tool` invocation in `call()`:

```python
    try:
        result = asyncio.run(mcp.call_tool(tool_name, parsed_arguments))
    except ToolError as exc:
        cause = exc.__cause__
        message = str(exc)
        if message.startswith("Unknown tool: "):
            typer.echo(message, err=True)
        elif isinstance(cause, PydanticValidationError):
            typer.echo(f"Invalid arguments for {tool_name}: {cause}", err=True)
        else:
            typer.echo(f"Error calling {tool_name}: {cause if cause is not None else exc}", err=True)
        raise typer.Exit(1) from exc
    except MCPError as exc:
        typer.echo(f"Error calling {tool_name}: {exc}", err=True)
        raise typer.Exit(1) from exc

    payload = result.structured_content if result.structured_content is not None else result.content
    typer.echo(json.dumps(payload, indent=2, default=str))
```

(This replaces the bare `result = asyncio.run(...)` line from Task 4 with the `try/except` version; the two lines after it are unchanged.)

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_mcp_server_cli.py -v`
Expected: all PASS, including Task 4's success-path test and every earlier task's tests (full regression check).

- [ ] **Step 5: Commit**

```bash
git add taiga/mcp_server/cli.py tests/test_mcp_server_cli.py
git commit -m "feat(mcp): add error handling to taiga-mcp-server's 'call' subcommand"
```

---

## Task 6: Docs, changelog, and spec precision amendment

**Files:**
- Modify: `docs/mcp.rst`
- Modify: `AGENTS.md`
- Create: `changes/14039.feature`
- Create: `changes/14039.removal`
- Modify: `artifacts/specs/2026-08-31-mcp-cli-parity-design.md`

**Interfaces:** none (documentation-only task).

- [ ] **Step 1: Update `docs/mcp.rst`'s "Running the server standalone" example**

At `docs/mcp.rst:93-98`, change:

```rst
.. code:: shell

    TAIGA_HOST=https://taiga.example.com \
    TAIGA_USERNAME=myuser \
    TAIGA_PASSWORD=mypassword \
    taiga-mcp-server
```

to:

```rst
.. code:: shell

    TAIGA_HOST=https://taiga.example.com \
    TAIGA_USERNAME=myuser \
    TAIGA_PASSWORD=mypassword \
    taiga-mcp-server serve
```

- [ ] **Step 2: Update the "Connecting an MCP client" example**

At `docs/mcp.rst:113-119`, change the last line of the `claude mcp add` block from:

```rst
      -- taiga-mcp-server
```

to:

```rst
      -- taiga-mcp-server serve
```

- [ ] **Step 3: Add a new "Listing and calling tools directly" section**

Insert, right after the "Running the server standalone" section (after line 102, before the "Connecting an MCP client" heading at line 104):

```rst
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
```

- [ ] **Step 4: Update `AGENTS.md`**

At `AGENTS.md`, in the two `claude mcp add` examples in step 4 (lines ~81-101), append ` serve` to the command in both:

```bash
   claude mcp add --scope user taiga \
     -e TAIGA_HOST=https://my.taiga.com \
     -e TAIGA_USERNAME=<username> \
     -e TAIGA_PASSWORD=<password> \
     -- /absolute/path/to/taiga-mcp-server serve
```

```bash
   claude mcp add --scope user taiga \
     -e TAIGA_HOST=https://my.taiga.com \
     -e TAIGA_TOKEN=<token> \
     -- /absolute/path/to/taiga-mcp-server serve
```

```bash
   claude mcp add --scope user taiga \
     -e TAIGA_HOST=https://my.taiga.com \
     -e TAIGA_TOKEN=<token> \
     -- uvx --from "python-taiga[mcp]" taiga-mcp-server serve
```

- [ ] **Step 5: Add towncrier changelog fragments**

Create `changes/14039.feature`:

```
Add `list-tools` and `call` subcommands to `taiga-mcp-server`, letting tools be listed and invoked directly from a shell without an MCP client.
```

Create `changes/14039.removal`:

```
`taiga-mcp-server` now requires an explicit `serve` subcommand to start the MCP server. Running the bare command with no subcommand no longer starts it (it shows the command list instead) - update any MCP client configuration invoking it with no arguments to add ` serve`.
```

- [ ] **Step 6: Amend the spec's bare-invocation wording for accuracy**

In `artifacts/specs/2026-08-31-mcp-cli-parity-design.md`, in the "Breaking change" section, replace:

```
**This design makes `serve` an explicit, required subcommand** —
bare invocation becomes a Typer usage error. This was a deliberate choice
(matching ring's shape exactly) made during design, not a byproduct.
```

with:

```
**This design makes `serve` an explicit, required subcommand** — bare
invocation no longer starts the server. With Typer's `no_args_is_help=True`
(the same setting ring-mcp-server's own CLI uses), it shows the command
list/help and exits 0, rather than becoming a hard usage error — the
compatibility break is that it no longer silently defaults to `serve`, not
the exact exit code. This was a deliberate choice (matching ring's shape
exactly) made during design, not a byproduct.
```

- [ ] **Step 7: Commit**

```bash
git add docs/mcp.rst AGENTS.md changes/14039.feature changes/14039.removal artifacts/specs/2026-08-31-mcp-cli-parity-design.md
git commit -m "docs(mcp): document taiga-mcp-server's new serve/list-tools/call subcommands"
```

---

## Task 7: Final full-suite regression check

**Files:** none (verification only).

- [ ] **Step 1: Run the full test suite**

Run: `tox -e py313`
Expected: all tests PASS, including every test from Tasks 2–5 and the pre-existing suite (`test_mcp_server.py`, `test_mcp_server_auth.py`, and the rest of the repo's tests untouched by this plan).

- [ ] **Step 2: Run linting**

Run: `tox -e ruff,black,isort` (the three lint/format-check envs defined in `tox.ini`) against the full repo.
Expected: no violations on `taiga/mcp_server/cli.py` or `tests/test_mcp_server_cli.py`. If `black`/`isort` report formatting diffs, run `tox -e blacken,isort_format` to auto-fix, then re-run the check envs.

- [ ] **Step 3: Confirm no unintended changes to untouched files**

Run: `git diff --stat feature/issue-267-add-mcp..HEAD`
Expected: only the files listed in this plan's "File Structure" table appear.
