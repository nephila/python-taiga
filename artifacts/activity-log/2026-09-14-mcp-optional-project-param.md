## 2026-09-14 — Made `project` optional on `list_milestones`/`list_wiki_pages` in the MCP server
**What:** Audited every `project`-taking tool in `taiga/mcp_server/server.py` against
what the underlying python-taiga client/API actually requires. `list_milestones` and
`list_wiki_pages` required `project` but the underlying `Milestones.list()` /
`WikiPages.list()` calls are unconstrained `ListResource.list(**queryparams)` — no
required args. Confirmed live against `https://taiga.nephila.it` (auth via
TAIGA_USER/TAIGA_PASSWORD): both list calls succeed with no `project` filter,
returning cross-project results (1246 milestones, 94 wiki pages). Made `project`
optional on both, mirroring the existing `list_user_stories`/`list_tasks`/
`list_issues`/`list_epics` pattern (`project: str | int | None = None`, added to the
query only when given). Everything else audited (ref-based `by_ref` lookups,
`search`, `list_memberships`, all `create_*` calls) genuinely requires `project` at
the API level and was left untouched. Updated `docs/mcp.rst` for the two changed
tools to match.
**Why:** User request via `/nephila-flow`: "verify in MCP server, where project
parameter is really required by the underlying API. when not required, make it
optional."
**Decisions:** Treated this as a lightweight adaptation of the flow (agreed with the
user up front) rather than the full 11-step lifecycle — no formal brainstorming/spec
or written plan doc, since it's a small, well-scoped verification+fix, not a new
feature; kept branch/TDD/review/wrap-up/commit-review steps as normal. Skipped the
towncrier changelog fragment (CONTRIBUTING.rst requires fragment names to reference
a real issue number; none exists for this minor fix and GitHub MCP wasn't connected
to create/look one up) — user's explicit call when asked.
**Agent usage:**

| Stage | Agent/skill | Tokens | Time |
|---|---|---|---|
| Review | superpowers:requesting-code-review (general-purpose subagent) | ~79k | ~70s |

**Considered & dropped:** Re-verifying every "genuinely required" tool live against
the real API too — judged unnecessary since those are structurally required by the
client library's own signatures/hardcoded query params (`by_ref` endpoint, `search`,
`Project.list_memberships`), not just conventionally passed; the review subagent
independently spot-checked that reasoning against `taiga/client.py` and
`taiga/models/models.py` and confirmed it.
**Follow-ups:** None outstanding — review verdict was "Ready to merge: Yes" with no
Critical/Important issues.
**Refs:** Branch `issue/mcp-optional-project-param`, off `feature/issue-267-add-mcp`.
Eval: 94% — artifacts/evaluations/2026-09-14-mcp-optional-project-param.md
