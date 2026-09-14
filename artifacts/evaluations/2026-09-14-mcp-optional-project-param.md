# Evaluation — mcp-optional-project-param

- **Date:** 2026-09-14
- **Branch:** issue/mcp-optional-project-param (working tree, uncommitted, vs HEAD 05c846f)
- **Task:** verify where `project` is really required by the underlying Taiga API in the MCP server; make it optional where it isn't
- **Coverage:** full — both changed files (`taiga/mcp_server/server.py`, `tests/test_mcp_server.py`) read in full; whole audit of every `project`-taking tool in `server.py` performed and independently spot-checked by a review subagent

## Scores
| Dimension | Score | Weight | Key evidence |
|---|---|---|---|
| Functionality | 5 | 20 | Verified live against `https://taiga.nephila.it`: `milestones.list()`/`wikipages.list()` succeed with no `project` (1246/94 items); fix mirrors sibling `list_user_stories`/`list_tasks`/`list_issues`/`list_epics` exactly (server.py:294-303 vs new list_milestones/list_wiki_pages) |
| Testing | 5 | 15 | RED confirmed (`TypeError: missing 1 required positional argument: 'project'`) before GREEN; `_no_project`/`_with_project` pairs added for both functions; real `assert_called_once_with(...)` assertions, not tautological mocks; full suite 340/340 pass |
| Security | 5 | 15 | No new trust-boundary input handling beyond existing `_resolve_project_id`; no secrets, no injection-prone construction |
| Code quality & best practices | 5 | 15 | `ruff check`, `black --check`, `isort --check` all clean; change is a byte-for-byte pattern match to existing sibling functions, no dead code |
| Maintainability & flexibility | 5 | 15 | Single-purpose, minimal diff (16 lines in server.py), no new coupling |
| Error handling | 4 | 10 | No new failure paths introduced; `project=0` edge case correctly handled via `is not None` (not truthiness) check, verified by review subagent |
| Documentation | 3 | 10 | Docstrings on both changed functions updated ("optionally scoped to a project"); `docs/mcp.rst` entries for `list_milestones`/`list_wiki_pages` not yet updated and no towncrier changelog fragment added — flagged by review as the only outstanding minor items, to be closed by doc-sync next |

## Recommendations
- Documentation: update `docs/mcp.rst`'s `list_milestones`/`list_wiki_pages` lines to mention optional project scoping, and add a towncrier changelog fragment — handled next via the doc-sync step.

## Total
**94%** — Correct, well-tested, low-risk fix; only the not-yet-run doc-sync pass keeps Documentation below top marks.
