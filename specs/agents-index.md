# Agent Index

> Related specs: [architecture](architecture.md) · [workflows](workflows.md)

This file lists every AI agent in the system, the prompt file it runs from, the recommended model, and what it does. Where functionality can be implemented as a deterministic Python script instead of an AI agent, it is noted here and kept out of the agent list.

---

## AI Agents

### Orchestrator

| | |
|---|---|
| **Prompt file** | `prompts/orchestrator.md` |
| **Model** | `claude-sonnet-4-6` |
| **Spawned by** | User script (`vatic inbox`) |
| **Runs** | Once per `vatic inbox` invocation |

Reads all files in `inbox/`, understands their content, and spawns one Quick Search sub-agent per inbox file (in parallel via the `Agent` tool). Collects results from all sub-agents and emits a single JSON work plan to stdout.

Does not write files. Does not decide create-vs-update. Does not read existing vault notes beyond their `summary` property.

---

### Quick Search

| | |
|---|---|
| **Prompt file** | `prompts/quick-search.md` |
| **Model** | `claude-haiku-4-5-20251001` |
| **Spawned by** | Orchestrator (via `Agent` tool, in parallel) |
| **Runs** | Once per inbox file |

Given the content of one inbox file, generates search queries and runs them against the vault using the obsidian CLI. Reads the `summary` property of results to filter for relevance. Returns a short JSON list of related vault file paths. Task is mechanical enough for Haiku — no writing, no judgment beyond relevance filtering.

---

### Editor

| | |
|---|---|
| **Prompt file** | `prompts/editor.md` |
| **Model** | `claude-sonnet-4-6` |
| **Spawned by** | User script (one `nono run` per inbox file, in parallel) |
| **Runs** | Once per inbox file |

The main writing agent. Receives one inbox file, its related vault files, and any answered review questions. Decides how to decompose the content into atomic notes, writes each note to its staging subdirectory, and writes `_review.md` for any questions it cannot resolve. Prefers decomposition — one concept per note, cross-linked with `[[wikilinks]]`.

Upgrade to `claude-opus-4-7` if output quality on complex multi-topic articles is insufficient.

---

### Q&A Search

| | |
|---|---|
| **Prompt file** | `prompts/qa-search.md` |
| **Model** | `claude-haiku-4-5-20251001` |
| **Spawned by** | Q&A Composer (via `Agent` tool) |
| **Runs** | Once per `vatic ask` invocation |

Given a question, generates search queries, runs them via the obsidian CLI, reads `summary` properties of results, and returns a ranked list of relevant vault file paths. Returns paths only — no file content loaded. Keeps context window small and cost low.

---

### Q&A Composer

| | |
|---|---|
| **Prompt file** | `prompts/qa-composer.md` |
| **Model** | `claude-sonnet-4-6` |
| **Spawned by** | User script (`vatic ask`) |
| **Runs** | Once per `vatic ask` invocation |

Receives the user's question and the ranked file list from Q&A Search. Reads the full content of the top-ranked notes and composes a grounded answer with a Sources section. If `--save` is passed, writes output to its pre-created `queries/` slot.

Split from Q&A Search so the search step stays context-light (summaries only) while the composition step loads full note content without contaminating a shared context window.

---

## Python Scripts (not AI)

These tasks are deterministic enough to implement without AI. Keeping them as scripts reduces cost, latency, and failure surface.

| Script | Purpose |
|---|---|
| `scripts/pre-screen.py` | Checks each inbox file before spawning an Editor: detects bare URLs (regex) and empty/unreadable files. Adds a review entry directly and skips the agent entirely for those files. |
| `scripts/check-review.py` | Parses `_meta/review.md`, finds entries matching a given inbox file, checks whether each `> Answer:` line is filled. Returns structured data to the script; computes `REVIEW_HAS_ANSWERS`. |
| `scripts/commit-staging.py` | Reads all staging subdirectories after agents complete. Validates `target` paths, strips `staging:` blocks, moves files to vault, appends `_review.md` entries to `_meta/review.md`, appends new tags to `_meta/tags.md`, removes processed inbox files, cleans up staging. |

---

## Prompt file frontmatter

Every prompt file in `prompts/` carries frontmatter that the launch script reads to select the correct model and pass any static configuration:

```yaml
---
model: claude-haiku-4-5-20251001
agent: quick-search
spawned-by: orchestrator
---
```

The script passes the `model` value to `claude --model <model> --print`.
