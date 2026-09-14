## 2026-09-14 — Added `include_user_stories` toggle to `list_milestones`/`get_milestone`
**What:** Added `include_user_stories: bool = True` to the MCP server's
`list_milestones` and `get_milestone` tools. `Milestone.user_stories` is always
fully expanded by python-taiga's parser into complete `UserStory` objects, which
`to_jsonable()` then serializes in full — so the embedded field can be large.
When `include_user_stories=False`, a new `_strip_user_stories()` helper pops that
key from each returned milestone dict (handles both the list shape from
`list_milestones` and the single-dict shape from `get_milestone`). Default `True`
preserves today's output exactly for existing callers. Updated `docs/mcp.rst`,
splitting the milestone tools' doc entry so the two changed tools get their own
line mentioning the flag.
**Why:** User request via `/nephila-flow`: "add to
taiga.mcp_server.server.list_milestones the option to return the full taiga
response for the given endpoint or to remove user_stories attribute from returned
data."
**Decisions:** Classified as "bounded" per superpowers:brainstorming (existing
tool, new flag) — short in-chat design instead of a written spec/plan doc, then
straight to TDD implementation; matches the same-day precedent from
[[2026-09-14-mcp-optional-project-param]]. Confirmed with the user that "full
Taiga response" meant one toggle (embed vs. strip `user_stories`), not a
raw/unparsed API passthrough. Extended the flag to `get_milestone` too (not just
`list_milestones` as literally asked) since it shares the identical
embedded-`user_stories` issue — user's explicit call when asked. Default `True`
chosen over `False` to avoid a breaking change to existing callers' output shape.
**Agent usage:**

| Stage | Agent/skill | Tokens | Time |
|---|---|---|---|
| Review | superpowers:requesting-code-review (general-purpose subagent) | ~70k | ~60s |

**Considered & dropped:** N/A — single clear approach, no alternatives seriously
weighed beyond the toggle-meaning clarification above.
**Follow-ups:** Review flagged two Minor nits (helper's `Any` type hint too broad;
no direct unit test of the helper) — both applied immediately as a follow-up commit
(narrowed the type hint, added 3 direct unit tests) rather than deferred.
**Refs:** Branch `issue/mcp-milestone-user-stories-toggle`, off
`issue/mcp-optional-project-param` (itself off `feature/issue-267-add-mcp`), not yet
merged/pushed.
Eval: 94% — artifacts/evaluations/2026-09-14-mcp-milestone-user-stories-toggle.md
