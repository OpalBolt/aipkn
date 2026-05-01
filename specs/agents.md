# Agent Descriptions

> Related specs: [architecture](architecture.md) · [data-model](data-model.md) · [workflows](workflows.md)

---

## Orchestrator agent

**Responsibilities:**
- Read all files in `inbox/` and the current tag list from `_meta/tags.md`
- For each inbox file: read its content, search the vault for related topics using the obsidian CLI, read the `summary` property of search results to assess relevance
- Emit a JSON work plan to stdout — one entry per inbox file

**What it does NOT do:** Decide whether to create a new note or update an existing one. That decision belongs to the file agent, which has the full content of the related files. The orchestrator only surfaces *which* vault files are relevant; it does not prescribe an action. It also does not write any files, does not spawn `nono run`, and does not touch staging.

The orchestrator may use Claude's `Agent` tool internally to parallelise vault searches across inbox files — those sub-agents inherit the same read-only sandbox.

**JSON work plan (stdout):**
```json
[
  {
    "inbox_file": "inbox/item.md",
    "related_vault_files": [
      "notes/existing-a.md",
      "notes/existing-b.md"
    ]
  }
]
```

All paths are relative to `$VAULT`. The script validates every path before use.

---

## File agent (one per inbox file)

**Responsibilities:**
- If `REVIEW_HAS_ANSWERS` is `true`: read `_meta/review.md`, act on any answered entries matching its inbox file, remove those entries from `review.md`
- Read the assigned inbox file
- Read all related vault files provided in the work plan entry
- Decide how to decompose the content: one inbox item may produce multiple output notes across different vault folders (e.g. an article that introduces a concept worth its own atomic note, triggers an update to an existing project note, and is itself archived in `articles/`)
- Write one staging file per output note to its assigned staging subdirectory
- If any question cannot be resolved without user input: write a `_review.md` file to the staging subdirectory with the question(s) — the script appends these to `_meta/review.md`

**Default behaviour: prefer decomposition.** If an inbox item touches multiple distinct topics, split it into atomic notes rather than cramming everything into one. Each atomic note should cover exactly one concept. Cross-link related output notes using `[[wikilinks]]` in the `links` field.

**What it does NOT do:** Write to vault content folders, write new entries directly to `_meta/review.md`, remove inbox files, or communicate with other file agents. It has no knowledge of other inbox items.

### Staging file format

The agent writes one Markdown file per output note into its staging subdirectory. Each file has a `staging` block (instructions for the script) followed by standard note frontmatter and content:

```yaml
---
staging:
  action: create | update | drop | needs-review
  target: notes/some-note.md       # relative to $VAULT; required for create/update
  new_tags:                        # any tags not in _meta/tags.md
    - tag: machine-learning
      definition: "..."
title: Some Note
date: YYYY-MM-DD
type: note | article | project | task | resource
tags: []
summary: "..."
source: "..."
links: []
---

# Note content here
```

The `staging` block is consumed by the script and stripped before the file is written to the vault. For `update`, the agent writes the complete replacement content of the target note (it has read access to the existing note and produces the merged result). For `drop`, the file body may be empty.

### Review questions format (`_review.md` in staging)

If the agent has questions for the user, it writes a `_review.md` file to its staging subdirectory. Each question follows the format from [data-model](data-model.md#review-queue-format):

```markdown
- **[inbox/some-file.md | 2026-05-01]** Question text here?

  > Answer:

---
```

The script appends all `_review.md` entries to `_meta/review.md` after agents complete.

### Example decomposition

A clipped article about a new database architecture might produce:
- `articles/distributed-sql-overview.md` (`action: create`) — the archived article itself
- `notes/consensus-algorithms.md` (`action: create`) — atomic note on a concept introduced in the article
- `notes/cap-theorem.md` (`action: update`) — existing note extended with new nuance from the article
- `projects/db-migration-2026.md` (`action: update`) — existing project note updated with a relevant reference

---

## Q&A agent

The Q&A workflow is a single agent — no sub-agents needed. One question maps to one bounded context: search, filter by summary, read relevant notes, answer. If the vault grows large enough that reading all relevant notes exceeds context, introduce a retrieval sub-agent that reads and scores notes, returning only the top N to the answering agent.

See [workflows](workflows.md#workflow-2-qa-ai-ask) for the full step-by-step.
