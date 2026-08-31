# Design: CLI parity between python-taiga's MCP server and ring-mcp-server

Date: 2026-08-31
Status: Approved (design phase). Implementation plan to follow in this repo.
Origin: analysis and design were done from the `ring-mcp-server` repository
(comparing this project's `taiga/mcp_server/` against `ring-mcp-server`'s
CLI), then handed off and moved here since this is where the actual
implementation belongs. Taiga: us-14039. GitHub issue: 14039.

## Context

`ring-mcp-server` (github.com/nephila/ring_mcp) and this repo's
`taiga/mcp_server/` package are both MCP servers for Nephila tooling, but
architecturally opposite by design:

- **ring-mcp-server**: generates its entire MCP tool set dynamically at
  startup from a bundled OpenAPI 3.0 spec (`ring_mcp/spec.py`,
  `ring_mcp/tools.py`). Tool names are the spec's `operationId`s verbatim
  (dashes → underscores). This is intentional to that project and out of
  scope here.
- **python-taiga** (this repo): hand-implements each of its ~45 (48
  including cross-cutting ones) Taiga operations as an individually
  authored `@mcp.tool()`-decorated function in `taiga/mcp_server/server.py`,
  using the official MCP SDK's `MCPServer` (`mcp.server.mcpserver`,
  `mcp==2.0.0`). Tool name/description/input schema are all derived by the
  SDK from the function signature and docstring. **This architecture must
  not change** — that was an explicit constraint on this design.

What differs today, and what this design closes, is the **CLI surface**:
ring-mcp-server exposes its full tool set through a small, fixed set of
generic CLI subcommands usable directly from a shell without an MCP client
(`serve`, `list-tools`, `call <operation_id> --json`, `fetch-token`).
`taiga-mcp-server` today does exactly one thing — start the MCP stdio
server — with no way to list or invoke a tool from a shell at all.

## Goal

Give `taiga-mcp-server` the same **CLI verb shape** and **invocation
method** as `ring-mcp-server`, without touching this repo's core
architecture (each Taiga operation stays a hand-written `@mcp.tool()`
function; no dynamic generation is introduced).

## Non-goals (explicitly out of scope, confirmed during design)

- **No renaming of existing tools.** The ~45 tool functions
  (`list_user_stories`, `get_issue`, `create_task`, etc.) and their
  parameters/`ref`-vs-`_by_id` addressing convention are untouched. Parity
  is scoped to the CLI verbs and the JSON-blob invocation method only, not
  to reshaping tool names toward ring's OpenAPI-operationId-identity style.
- **No `fetch-token` equivalent.** `auth.build_client()` already resolves
  username/password to a session token internally and lazily on first tool
  call. Taiga JWTs are typically short-lived (per this repo's own
  `AGENTS.md`), so a separately printed, exportable token doesn't carry its
  weight the way ring's DRF token does. Skipped.
- **No change to `taiga/mcp_server/server.py`'s tool bodies, `auth.py`'s
  credential-resolution logic, or `serialize.py`.** This design touches only
  `taiga/mcp_server/cli.py` (rewritten) and its tests/docs.

## Breaking change (must be called out prominently)

Today, bare `taiga-mcp-server` (no arguments) always starts the MCP stdio
server. **This design makes `serve` an explicit, required subcommand** —
bare invocation becomes a Typer usage error. This was a deliberate choice
(matching ring's shape exactly) made during design, not a byproduct.

Impact: every existing MCP client config that invokes the binary with no
arguments (e.g. the `claude mcp add --scope user taiga ... -- taiga-mcp-server`
and `uvx --from "python-taiga[mcp]" taiga-mcp-server` examples currently
documented in this repo's own `AGENTS.md`) breaks and must add ` serve`.
This needs:

- A major-version bump per this repo's own versioning/release mechanism
  (`bump-my-version` per one of the branch names seen in `git branch -a` —
  confirm exact tool/config during plan execution).
- A prominent breaking-change note in the CHANGELOG/release notes.
- Updated examples in `docs/mcp.rst` and `AGENTS.md` (see "Docs" below).

## Design

### 1. CLI structure (Typer)

Rewrite `taiga/mcp_server/cli.py` from `argparse` to **Typer** (a new
dependency for this repo, chosen deliberately for implementation-style
consistency with ring-mcp-server over keeping argparse, per explicit design
decision — trade-off: one new runtime dependency plus rewriting the existing
flag-parsing logic).

Three subcommands:

```
taiga-mcp-server serve
    [--host HOST] [--token TOKEN] [--token-type TYPE]
    [--username USER] [--password PASS] [--tls-verify/--no-tls-verify]

    Same auth flags, same env-var fallback (TAIGA_HOST/TAIGA_TOKEN/
    TAIGA_TOKEN_TYPE/TAIGA_USERNAME/TAIGA_PASSWORD/TAIGA_TLS_VERIFY), same
    precedence (flag > env > default) as today's argparse implementation.
    Calls auth.configure(...), then mcp.run(transport="stdio"). Behavior is
    identical to today's default flow — only the verb is new.

taiga-mcp-server list-tools [--verbose/-v]
    [same auth flags as serve, for consistency — list-tools itself never
     calls get_client(), so credentials aren't actually required to run it,
     but auth.configure() is still invoked for a uniform command surface]

    Default: one line per tool, "name\tdescription", sorted by name.
    --verbose: also pretty-prints each tool's JSON input schema.

taiga-mcp-server call <tool_name> --json/-j '<json>'
    [same auth flags as serve — required here since most tools call
     get_client()]

    Parses --json (default "{}") as the arguments dict, invokes the named
    tool in-process, prints the JSON result to stdout, or an error to
    stderr with exit code 1.
```

Each subcommand keeps its own copy of the auth option set (via a shared
Typer callback or small options dataclass) rather than global
pre-subcommand flags — idiomatic Typer, and keeps `serve`'s flag behavior
byte-for-byte compatible with today aside from requiring the verb.

### 2. Invocation mechanics (verified against the installed SDK)

`mcp.server.mcpserver.MCPServer` (`mcp==2.0.0`) is a distinct, purpose-built
class — not a `FastMCP` alias — exposing async in-process APIs confirmed by
direct inspection/execution against this repo's real `mcp` object
(`taiga.mcp_server.server.mcp`, using the `.tox/py313` env, which has the
`[mcp]` extra installed), with no live MCP client/transport round trip
required:

```python
async def list_tools(self) -> list[mcp_types.Tool]: ...
async def call_tool(self, name: str, arguments: dict[str, Any],
                     context=None) -> CallToolResult | InputRequiredResult: ...
```

**`list-tools`:**
```python
tools = asyncio.run(mcp.list_tools())
for t in sorted(tools, key=lambda t: t.name):
    dumped = t.model_dump(by_alias=True, exclude_none=True)
    print(f"{dumped['name']}\t{dumped.get('description', '')}")
    if verbose:
        print(json.dumps(dumped["inputSchema"], indent=2))
```
`model_dump(by_alias=True, exclude_none=True)` yields the wire-shaped keys
(`name`, `description`, `inputSchema`, `outputSchema`) exactly as an MCP
`ListTools` response would. Verified live: 48 tools registered today, e.g.
```json
{"name": "whoami", "description": "Return the Taiga user currently authenticated.",
 "inputSchema": {"properties": {}, "title": "whoamiArguments", "type": "object"},
 "outputSchema": {"additionalProperties": true, "title": "whoamiDictOutput", "type": "object"}}
```

**`call`:**
```python
arguments = json.loads(json_str)  # malformed JSON -> caught separately, see below
try:
    result = asyncio.run(mcp.call_tool(tool_name, arguments))
except ToolError as e:
    ...  # see error table below
else:
    payload = result.structured_content if result.structured_content is not None else result.content
    json.dump(payload, sys.stdout, indent=2, default=str)
```

`auth.configure(...)` runs before `asyncio.run(...)`, exactly as `serve`
does today, so `get_client()` inside tool bodies resolves credentials the
same way it does under a real MCP client.

### 3. Error handling & output contract

Mirrors ring's stderr-message-plus-`typer.Exit(1)` contract, mapped onto
this repo's actual failure shapes (all verified by direct execution against
the real `mcp` object during design):

| Failure | Detection | stderr message |
|---|---|---|
| Malformed `--json` | `json.JSONDecodeError` | `Invalid JSON in --json: {exc}` |
| Unknown tool name | `ToolError` message starts with `"Unknown tool: "` | printed as-is |
| Argument validation failure | `ToolError` with `e.__cause__` a `pydantic_core.ValidationError` | `Invalid arguments for {tool_name}: {cause}` |
| Tool raised an application exception (`ConfigError`, `TaigaRestException`, etc.) | `ToolError` with any other `e.__cause__` | `Error calling {tool_name}: {cause}` (fallback to `str(e)` if `__cause__` is `None`) |
| Missing/invalid credentials at `serve`/`call` startup | `ConfigError` from `auth.build_client()` | `{exc}` (message already clear per `auth.py`) |
| Anything from `mcp.shared.exceptions.MCPError` (unwrapped by `call_tool()` per the SDK's own re-raise) | caught for safety even though not expected in normal use | same generic "Error calling {tool_name}: {cause}" formatting |

All of the above: message to stderr, `raise typer.Exit(1)`.

Verified failure shapes, captured live against the real `mcp` object
(against `whoami`, an unknown tool, and `get_project` with a missing
required argument):

```python
await mcp.call_tool("whoami", {})
# ToolError: "Error executing tool whoami: The Taiga MCP server has not
#             been configured with any credentials."
# e.__cause__ -> ConfigError(...)

await mcp.call_tool("this_tool_does_not_exist", {})
# ToolError: "Unknown tool: this_tool_does_not_exist"

await mcp.call_tool("get_project", {})   # missing required "project" arg
# ToolError: "Error executing tool get_project: 1 validation error for
#             get_projectArguments ..."
# type(e.__cause__) -> pydantic_core.ValidationError
```

On success: `call` prefers `result.structured_content` (populated for every
tool here, since they all return dicts/lists via `to_jsonable()`), falling
back to `result.content` only if `structured_content` is `None`. Verified
live (with `get_client()` stubbed, since no live Taiga credentials were
available during design):
```python
result = await mcp.call_tool("whoami", {})
# type(result) -> mcp_types._types.CallToolResult
# result.structured_content -> {'id': 1, 'username': 'demo'}
# result.is_error -> False
```
Written via `json.dump(payload, sys.stdout, indent=2, default=str)`.

### 4. Testing (scope; exact fixtures/layout to be confirmed against this
repo's existing `tests/` conventions when the plan is written)

- **`serve`**: port existing argparse-flag-precedence tests to Typer's
  `CliRunner`; add a test asserting bare invocation (no subcommand) now
  exits non-zero instead of serving.
- **`list-tools`**: all tool names present, sorted; `--verbose` includes
  each tool's `inputSchema`; runs without any credentials configured (never
  calls `get_client()`).
- **`call`**: success path (stub/monkeypatch `get_client()`, assert stdout
  JSON matches the tool's return value); malformed `--json`; unknown tool
  name; missing required argument; tool-internal exception (e.g.
  unconfigured-credentials `ConfigError`) — each asserting the exact stderr
  message and exit code 1.
- No live network/Taiga server needed anywhere — everything runs in-process
  against `mcp` with `get_client`/`TaigaAPI` stubbed, as verified during
  design.

### 5. Docs & migration

- `docs/mcp.rst`: update every example showing bare `taiga-mcp-server` to
  `taiga-mcp-server serve`; add a new subsection documenting `list-tools`
  and `call`, styled after ring-mcp-server's own usage docs.
- `AGENTS.md`: update the two `claude mcp add ... -- taiga-mcp-server` /
  `-- uvx --from "python-taiga[mcp]" taiga-mcp-server` examples (step 4) to
  append ` serve`.
- CHANGELOG/release-notes mechanism for this repo (confirm exact convention
  during plan execution) documenting the breaking change.

## Open items for the implementation plan (not blocking this design)

- Confirm this repo's exact test directory layout/fixtures for
  `taiga/mcp_server/` before writing test cases.
- Confirm this repo's exact versioning/changelog mechanism for recording
  the breaking change (a `chore/issue-140-switch-to-bump-my-version` branch
  was seen in `git branch -a`, suggesting `bump-my-version` — verify).
- Confirm the Typer dependency is added correctly to `setup.cfg`'s `[mcp]`
  extras (alongside the existing `mcp~=2.0` pin).
- This branch (`feature/issue-14039-taiga-mcp-cli-parity`) is based on
  `feature/issue-267-add-mcp` (where `taiga/mcp_server/` currently lives,
  unmerged to `master`) rather than `master` itself, since the package
  doesn't exist on `master` yet. Rebase onto `master` once issue-267 merges,
  before this branch is itself merged.
