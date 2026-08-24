# Evaluation — mcp-sdk-rewrite

- **Date:** 2026-08-24
- **Branch:** feature/issue-267-add-mcp (working tree, uncommitted)
- **Task:** #267 (follow-up: swap `fastmcp` for the official `mcp` SDK, `mcp~=2.0`)
- **Coverage:** partial — scoped to this task's diff only (`setup.cfg`, `taiga/mcp_server/server.py`, 2 files / 37+37 lines). Excludes the rest of the already-committed MCP feature on this branch, which was a separate prior deliverable.

## Priority findings
- Documentation ≤ 2: `docs/mcp.rst:24-25` still describes `fastmcp` as the pulled-in dependency, contradicting the code now on `mcp~=2.0` — fix is queued in the immediately-following doc-sync step.

## Scores
| Dimension | Score | Weight | Key evidence |
|---|---|---|---|
| Functionality | 5 | 20 | 66/66 tests pass against real `mcp~=2.0` in a scratch venv; stdio smoke test lists all 34 tools with instructions preserved verbatim. |
| Testing | 4 | 15 | Existing suite exercises every tool function directly and would fail at import if `MCPServer`/decorator form were wrong (reviewer confirmed); no explicit assertion of tool count/import success as a named test. |
| Security | 4 | 15 | No new input handling introduced; diff is import/class-name/decorator-form only (server.py:9,14,57...). |
| Code quality & best practices | 5 | 15 | Mechanical, minimal diff matching stated intent exactly; no stray bare `@mcp.tool` or leftover `fastmcp` refs (verified via grep). |
| Maintainability & flexibility | 5 | 15 | Matches upstream naming (`MCPServer`) rather than aliasing; drops one third-party dependency. |
| Error handling | N/A | 10 | Diff touches no error-handling paths (`auth.py`/`ConfigError` untouched). |
| Documentation | 2 | 10 | `docs/mcp.rst` still names `fastmcp` as the dependency (see priority finding above). |

## Recommendations
- Documentation: run doc-sync now to update `docs/mcp.rst`'s install-extra description and the `pypi.org/project/fastmcp` link.

## Total
**87%** — Clean, correctly-verified mechanical swap; the only real gap is a stale doc line already queued for the next step.
