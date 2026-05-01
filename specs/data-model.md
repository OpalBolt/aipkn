# Data Model

> Related specs: [overview](overview.md) · [agents](agents.md) · [workflows](workflows.md)

## Vault Structure

```
vault/
├── inbox/          # Raw inputs — files land here before processing
│   └── staging/    # Agent output staging area — never a final destination
├── notes/          # Atomic notes (processed outputs)
├── articles/       # Clipped web content, saved articles
├── projects/       # Project containers (one note per project, or a subfolder)
├── tasks/          # Actionable items
├── queries/        # Saved Q&A sessions (optional, on-demand)
└── _meta/
    ├── review.md   # Ambiguous inbox items awaiting user decision (single file)
    ├── tags.md     # Canonical tag definitions
    └── templates/  # Note templates
```

`inbox/staging/` is a temporary working area used during inbox processing. Each file agent gets its own subdirectory here (e.g. `inbox/staging/abc123/`) and may write as many output files as the content requires — a single article may decompose into several atomic notes across multiple vault folders. The user-controlled script is the only thing that moves files from staging into the vault proper. Staging is always empty outside of an active `ai inbox` run.

---

## Note Template & Properties

Every note uses YAML frontmatter. The `summary` field is mandatory — it is used for AI search relevance filtering without reading the full file.

```yaml
---
title: <human-readable title>
date: YYYY-MM-DD
type: note | article | project | task | resource
tags: []
summary: <1-2 sentence description of what this note contains>
source: <URL or filename if derived from external content>
links: []
---
```

---

## Tag Taxonomy

Tags are split into two categories: **type tags** (what the note is) and **topic tags** (what it's about). Type is also captured in the `type` frontmatter field for structured querying; tags are for cross-cutting concerns.

### Starter Set

| Tag | Meaning |
|---|---|
| `#ai` | Artificial intelligence, LLMs, agents |
| `#dev` | Software development, code, architecture |
| `#ops` | Infrastructure, DevOps, tooling |
| `#career` | Professional development, job, skills |
| `#learning` | Study material, courses, books |
| `#personal` | Personal life, non-work |
| `#business` | Business strategy, work context |
| `#needs-review` | Requires user input before finalizing |
| `#archived` | No longer active or relevant |

**Expansion policy:** A file agent may introduce a new topic tag if no existing tag fits. It declares the new tag and its definition in the `new_tags` field of the staging frontmatter. The script appends new tags to `_meta/tags.md` when committing — agents never write to `_meta/` directly. Tags must be single-word or hyphenated (e.g. `#machine-learning`). Type and status concerns stay in frontmatter `type`/status fields, not tags.

---

## Review Queue Format (`_meta/review.md`)

`review.md` is the shared channel between agents and the user for questions that cannot be resolved without human input. Agents add questions via staging; the user answers in place; agents clean up resolved entries on the next run.

### Entry format

Each entry is a bullet with a header, a question, and an answer field, followed by a separator:

```markdown
- **[inbox/some-file.md | 2026-05-01]** Should the section on consensus algorithms be merged
  into the existing "CAP Theorem" note, or kept as a standalone atomic note?

  > Answer:

---
```

When the user answers, they fill in the `> Answer:` line:

```markdown
- **[inbox/some-file.md | 2026-05-01]** Should the section on consensus algorithms be merged
  into the existing "CAP Theorem" note, or kept as a standalone atomic note?

  > Answer: Merge into CAP Theorem — it adds nuance without warranting a separate note.

---
```

### Rules

- One `---` separator between entries. The final entry also ends with `---`.
- An entry is **unanswered** if the `> Answer:` line is empty or contains only whitespace after the colon.
- An entry is **answered** if the `> Answer:` line has non-empty content after the colon.
- File agents act on answered entries that match their assigned inbox file, then remove the entire entry (question + answer + separator) from `review.md`.
- File agents never add new entries directly — new questions are written to `_review.md` in the agent's staging subdirectory and appended to `review.md` by the script after all agents complete.

### Boolean flag

Before spawning each file agent, the script checks whether `review.md` contains any answered entries and passes the result in the agent's prompt context:

```
REVIEW_HAS_ANSWERS: true | false
```

If `false`, the agent skips opening `review.md` entirely. If `true`, the agent reads `review.md`, finds entries matching its assigned inbox file, uses the answers to guide its decisions, and removes those entries.
