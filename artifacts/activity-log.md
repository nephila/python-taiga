# Activity Log

## 2026-08-24 — Swapped fastmcp for the official mcp SDK in the Taiga MCP server
**What:** Rewrote `taiga/mcp_server/server.py` to build on the official MCP Python
SDK's `MCPServer` (`mcp.server.mcpserver`, `mcp~=2.0`) instead of the third-party
`fastmcp` package; updated the `mcp` extra in `setup.cfg` and the `docs/mcp.rst`
dependency mention accordingly. On `feature/issue-267-add-mcp`, as a follow-up to
the MCP server added earlier on that same branch.
**Why:** User asked to rewrite the MCP server on the official SDK instead of the
`fastmcp` wrapper, specifically pinned to `mcp~=2.0`.
**Decisions:**
- Classified as a *bounded* change (brainstorming skill) — existing flow, small
  mechanical diff — so no spec/plan artifact, direct implementation after in-chat
  design approval.
- Confirmed by installing `mcp~=2.0` in a scratch venv: mcp 2.0 renamed
  `fastmcp.FastMCP`/`mcp.server.fastmcp.FastMCP` to `mcp.server.mcpserver.MCPServer`
  (no back-compat alias), and requires the `@mcp.tool()` call form — bare
  `@mcp.tool` raises `TypeError` at import time.
- Renamed to `MCPServer` throughout (chose over aliasing to `FastMCP`) to match
  upstream naming exactly, per user preference.
- Stayed on the existing `feature/issue-267-add-mcp` branch rather than cutting a
  new one — this is a continuation of the same feature, not new scope.
- Left the working tree uncommitted (per chosen commit strategy) pending user
  review before splitting into commits.
**Agent usage:**

| Stage | Agent/skill | Tokens | Time |
|---|---|---|---|
| Review | general-purpose (requesting-code-review) | ~82k | ~4m |
| Review | nephila-core-conventions:code-eval | ~5k | ~2m |
| Review | nephila-core-conventions:doc-sync | ~3k | ~1m |

**Considered & dropped:** low-level `mcp.server.lowlevel.Server` rewrite (hand-rolled
schemas/dispatch) — rejected as unnecessary boilerplate once the official SDK's
own FastMCP-equivalent (`MCPServer`) covered the same decorator ergonomics.
Aliasing the new class as `FastMCP` to minimize diff size — rejected in favor of
the real name for clarity to future readers.
**Follow-ups:** `docs/mcp.rst` was updated for the dependency description; no other
doc/config files referenced `fastmcp` by name. Optional (not done): an explicit
tool-count/import smoke test for the SDK swap, and a towncrier fragment for the
dependency change (feature is still unreleased on this branch, so not required).
**Refs:** #267. Eval: 87% — artifacts/evaluations/2026-08-24-mcp-sdk-rewrite.md
