---
name: no-dynamic-memory-schema
description: Rejected building an agentic schema-negotiation loop for the auto-memory type system — stick with fixed 4 types unless a real pain point shows up
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ffec908f-0d86-43b9-957c-04311d52e6c5
  modified: 2026-07-24T15:10:57.646Z
---

Don't build a dynamic/agentic schema-negotiation pipeline (Intent Agent → File Suggestion Agent → propose/refine/fact-check loop → multi-agent shared-state negotiation, ADK-style) for the `~/.claude` auto-memory type system. Keep the fixed 4 types (user/feedback/project/reference) as-is.

**Why:** Surfaced 2026-07-24 while comparing our agent-memory/auto-memory stack against DeepLearning.AI × Neo4j's "Agentic Knowledge Graph Construction" course (ADK multi-agent schema-negotiation pattern). Walked all 4 pieces of that pattern against our memory system — none earned their complexity:
- Intent-capture-for-schema: routing.md's Step 0 already captures task scope; a separate goal-capture step per memory write is friction with no payoff at our volume.
- File Suggestion Agent: doesn't map — memory entries are synthesized notes, not files selected from a corpus.
- Propose/refine/fact-check loop: only a sliver of value (a "type doesn't fit, ask before force-fitting" escape hatch) and even that was speculative — no real case had come up where the 4 types failed to fit.
- Shared-state multi-agent negotiation: spinning multiple agents to negotiate a type label for one memory entry is wrong scale — this is solo, low-frequency, inline work, not enterprise multi-source ingestion.
User's own call after walking through it: "drop ทิ้งให้หมด ลบเลย" — explicit reject, not just my recommendation.

Contrast: [[graphify]]'s fixed-schema-per-extractor approach was independently validated as correct (AST ground truth beats LLM-negotiated schema for code) — same YAGNI logic, different domain, same conclusion (fixed schema wins when the domain doesn't have real ambiguity).

**How to apply:** If this idea resurfaces (e.g. a future course/post about agentic schema construction prompts "should we do that too"), don't re-litigate from scratch — check first whether a *real* memory-save case has actually failed to fit the 4 types. Absent that, the answer is still no.
