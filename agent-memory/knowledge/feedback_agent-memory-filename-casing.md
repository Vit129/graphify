---
name: agent-memory-filename-casing
description: "Canonical casing for agent-memory/ root files — ALL uppercase (PLAYBOOK.md, SKILL-LOG.md, EVAL-STATE.md, INDEX.md), confirmed by user 2026-07-30, supersedes a 2026-07-25 lowercase-INDEX.md exception"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 04b57bd0-e45e-49d9-8b07-cd6d209a0800
  modified: 2026-07-30T00:00:00.000Z
---

`agent-memory/PLAYBOOK.md`, `SKILL-LOG.md`, `EVAL-STATE.md`, `INDEX.md` are ALL uppercase — this is
the real, established convention across the ecosystem, not a bug. There is no lowercase exception.

**Why (superseding the 2026-07-25 version of this memory):** That version claimed `index.md`
(lowercase) was a deliberate, separate exception, citing `~/.claude/scripts/setup/setupMemory.sh`
as evidence. On 2026-07-30, rebuilding `agent-memory/` for `Git/Personal/graphify` from
`skills/agent-memory/references/templates/` (itself lowercase `index.md` at the time) propagated
the lowercase into a live project, prompting a re-check. Two things broke the old evidence:
1. `scripts/setup/setupMemory.sh` (the cited source) is dead — it points to
   `~/.kiro/skills/meta-skills/agent-memory/references/templates/`, which no longer exists. It's
   also unreferenced by any current doc/rule (arrived via an old "sync from .kiro" commit, then
   orphaned) — not the active bootstrap script.
2. Real instance count across 9 projects: 7 use uppercase `INDEX.md` (QA-Automation-Coding-Course,
   agy-plugin-codex, Accountant-Learning, agy-plugin-cc, My-Investment-Port, kouen-terminal,
   Home-Assistant). Only `~/.claude`'s own global copy and today's graphify bootstrap were
   lowercase — both anomalies, not the convention.
User confirmed uppercase twice in the same turn (direct statement, then explicit answer
"INDEX.md, PLAYBOOK.md และอื่นๆ" to a clarifying question) after seeing this exact evidence —
overriding their own 2026-07-25 confirmation of the opposite.
Fixed 2026-07-30: renamed `skills/agent-memory/references/templates/index.md` → `INDEX.md`,
`~/.claude/agent-memory/index.md` → `INDEX.md`, `Git/Personal/graphify/agent-memory/index.md` →
`INDEX.md`, and every text reference in `CLAUDE.md`, `SKILL.md`, `scripts/setup-agent-memory.sh`
(new), `scripts/session-end.sh`, `~/.kiro/scripts/setup/setupMemory.sh`, `~/.kiro/AGENTS.md`.

**How to apply:** Never "fix" a casing mismatch on any agent-memory/ root file by lowering
references to match a lowercase file — the file is the anomaly, not the references. If a NEW
casing mismatch is found, check real project instances (not just one script's history — a script
can itself be dead/orphaned and misleading, as happened here) before deciding which side is
"wrong." A prior "confirmed by user" note is not immune to being superseded by a later, better-evidenced
correction from the same user — surface the conflict and ask again rather than silently trusting
the older note.
