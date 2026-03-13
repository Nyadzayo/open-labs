# fintech-labs — CLAUDE.md

## Tool output discipline (non-negotiable)

After EVERY tool call, return ONLY:
- 5-10 bullet summary (never raw output)
- Up to 8 `path:line` pointers
- At most 1 diff hunk (80 lines max)
- Logs: first error + 10 lines above/below (30 lines max)
- If >100 lines returned: summarize. Never forward raw.

Input discipline:
- Read tool: ALWAYS pass offset + limit. Max 80 lines per call.
- Grep tool: ALWAYS use head_limit: 10. Add glob or type filter.
- Bash tool: Pipe through | head -30 for long output.
- Subagents: Use for any exploration needing >3 tool calls.

## Project rules
- Fintech lab system: minimal executable slices, not frameworks
- Every lab must have: lab.py (marimo), tests, README.md
- Tests are the primary artifact — write tests first or alongside code
- FastAPI by default, Django only for Lab 09
- SQLite for MVP, PostgreSQL for production variants
- All code must pass: pytest, ruff, mypy
- Use fintech domain language: idempotency key, settlement, ledger, reconciliation
- marimo notebooks are the learning surface — first principles through reflection

## Environment variables
DATABASE_URL, REDIS_URL, KAFKA_BROKER_URL, WEBHOOK_SECRET, PROMETHEUS_PORT

## Quick commands
```bash
pytest labs/NN-lab-name/ -v            # Test one lab
pytest --tb=short                       # Test all labs
ruff check .                            # Lint
mypy labs/NN-lab-name/                  # Type check
marimo edit labs/NN-lab-name/lab.py     # Open lab notebook
```

## Module index (load only what you touch)

| Module | Purpose | Docs |
|--------|---------|------|
| shared/ | Conftest fixtures, test helpers | [shared/CLAUDE.md](shared/CLAUDE.md) |
| labs/01-idempotent-payments/ | Idempotency key dedup | [CLAUDE.md](labs/01-idempotent-payments/CLAUDE.md) |
| labs/02-webhook-processing/ | HMAC verification + dedup | [CLAUDE.md](labs/02-webhook-processing/CLAUDE.md) |
| labs/03-payment-state-machine/ | Payment lifecycle states | [CLAUDE.md](labs/03-payment-state-machine/CLAUDE.md) |

Dependency rule: Each module CLAUDE.md has a "Depends on" section.

### Policy docs
| Policy | Docs |
|--------|------|
| Context rules | [docs/ai/CONTEXT_RULES.md](docs/ai/CONTEXT_RULES.md) |

## Code style
- Formatter: ruff format (line-length 88)
- Linter: ruff check
- Type checking: mypy --strict on new code
- No docstrings required on lab code — READMEs document behavior
- Prefer explicit over clever

## Workflow
- One lab at a time, fully complete before starting next
- Test first or alongside — never after
- CI must be green before moving to next lab
- Commit per logical unit (not per file)

## Definition of done (per lab)
- [ ] All tests pass locally and in CI
- [ ] ruff + mypy clean
- [ ] README complete
- [ ] Confidence score logged in PROGRESS.md

## Compaction instructions
When compacting, ALWAYS preserve:
- Full list of files modified in this session
- All test commands run and their pass/fail results
- Current lab being worked on and which step
- Any error messages being debugged
- Contents of scratchpad file if one exists

## Scratchpad pattern
For any task requiring >5 tool calls:
- Create: /tmp/scratchpad-<lab-name>.md
- Update: after each major step
- Read: after compaction or /clear
- Delete: when lab is complete
