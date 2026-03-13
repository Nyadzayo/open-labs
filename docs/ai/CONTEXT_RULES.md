# Context Rules for AI Assistants

## Token-saving discipline
- Do NOT request or output full files. Use path + line ranges (max 80 lines).
- Do NOT dump raw HTML, network payloads, or long console logs.
- Prefer git diff hunks over re-pasting files.
- Before opening anything big, run a targeted search then open only that section.

## Task handling
- Start with: entry point(s) and smallest reproducible case.
- Propose minimal code change and exact files/lines to edit.
- After edits, run the smallest targeted test command.

## Tool output budget
- Small action (single file read, grep): 5 bullets + pointers.
- Medium action (multi-file search, test run): 8 bullets + 1 diff hunk.
- Large action (build output, deploy log): 10 bullets max.

## The 6 high-risk actions
| Risk action | Do instead |
|---|---|
| Echo full file after Read | Summarize + path:line pointers |
| Dump raw HTML/browser output | Extract relevant elements only |
| Full console/server logs | First error + 10 lines context |
| Full network request/response | Method, URL, status, 200 chars |
| Entire git diff | Per-file summary, 1 relevant hunk |
| Full directory tree | Top 8 paths, ask if more needed |

## Daily workflow
1. State goal (3 lines)
2. Locate: targeted search, open 20-80 line range
3. Read: always offset + limit
4. Edit: exact path:line, show only diff
5. Test: smallest test command, pass/fail + first error
6. Commit: 3-5 bullet summary
