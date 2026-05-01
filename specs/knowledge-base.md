# AI-Assisted Personal Knowledge Base

## Problem & Goals

Build a personal knowledge base on top of an existing Obsidian vault, where an AI agent (Claude) handles the cognitive overhead of organizing, linking, and surfacing knowledge. The goal is a system where:

- Capturing new knowledge requires minimal friction (drop a file, paste text, clip a page)
- The vault stays clean and connected without manual tagging or linking
- You can ask natural-language questions and get answers with direct references to source notes
- Everything operates from the terminal or Claude Code — no GUI required for the agent workflows

This repo (`AI-knowledge`) is **tooling only** — scripts, prompts, and Claude config. The Obsidian vault lives in a separate directory (path TBD, must be configured).

---

## Non-Goals

- Building a custom Obsidian plugin
- Replacing Obsidian as the reading/editing UI
- Real-time sync or background daemon (all workflows are manually triggered)
- Handling binary attachments (images, PDFs) in the first version

---

## Vault Structure

Design a clean folder hierarchy from scratch:

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

---

## Multi-Agent Architecture

All workflows run as a hierarchy of agents. The goal is to keep each agent's context window small and focused — no single agent loads the entire vault or holds all inbox files at once.

```
User / CLI
    │  (only this layer may invoke nono run)
    │
    ├─► Orchestrator session (nono: vault/ read-only)
    │       Reads inbox, searches vault, emits JSON work plan → stdout
    │       May spawn read-only sub-agents internally for parallel search
    │
    │   Script checks review.md → computes REVIEW_HAS_ANSWERS
    │   Script reads + validates JSON work plan
    │   Script pre-creates staging subdirectory per agent
    │
    ├─► File agent session × N (one nono run per inbox file)
    │       nono: vault/ (r) + inbox/$FILE (r) + inbox/staging/$AGENT_ID/ (rw)
    │       Writes one or more output files to its staging subdirectory
    │       Never touches vault content folders directly
    │
    │   Script reads staging files, validates paths, moves to vault
    │   Script updates _meta/tags.md and _meta/review.md
    │   Script removes processed inbox files
    │
    └─► Q&A agent session (nono: vault/ read-only [+ queries/$SLUG rw if --save])
```

Every agent runs inside a **nono sandbox**. Each sandbox is granted only the paths it actually needs — no agent can read or write beyond its declared scope. This is enforced at the OS level and cannot be bypassed from within the session.

**Critical security constraint:** The AI must never initiate a new `nono run`. Doing so would allow an agent to define its own sandbox permissions and expand its own access. `nono run` is exclusively invoked by the user-controlled script. Within a nono session, Claude may use the `Agent` tool to spawn sub-agents — those inherit the same sandbox and cannot expand it.

**No AI writes to the vault.** File agents write only to their assigned staging slot. The user-controlled script is the sole process that moves content into vault folders, updates `_meta/`, and removes inbox files. This ensures all vault mutations are deterministic, path-validated operations under user control.

---

## Sandbox Permissions (nono)

Paths follow the principle of least privilege. `--read` and `--read-file` are used wherever write access is not needed. `--allow-file` (read+write on a single file) is used for staging slots — never directory-level write on vault content folders.

### Orchestrator sandbox

```bash
nono run \
  --read $VAULT \                 # full vault read — inbox listing + obsidian CLI search
  -- claude --print "..." < orchestrator-prompt.md
```

The orchestrator gets full vault read (required for obsidian CLI to traverse the vault) and nothing else. It emits a JSON work plan to stdout — no files written. The script captures stdout.

### File agent sandbox (one per inbox file)

```bash
nono run \
  --read $VAULT \                               # full vault read — obsidian CLI search
  --read-file $VAULT/inbox/$FILE \              # the assigned inbox file
  --allow $VAULT/inbox/staging/$AGENT_ID/ \     # agent's private staging subdirectory
  --allow-file $VAULT/_meta/review.md \         # read answered questions + remove resolved entries
  -- claude --print "..." < file-agent-prompt.md
```

`$AGENT_ID` is a unique identifier generated by the script. The script creates the subdirectory before launching the session. The agent may write as many files as it needs within that subdirectory — one per output note. It cannot write outside its own staging subdirectory, cannot reach other agents' staging areas, and cannot touch vault content folders or other `_meta/` files.

`review.md` access is for reading user-provided answers and removing resolved entries only. New review questions are written to a `_review.md` file in the agent's staging subdirectory and appended to `_meta/review.md` by the script — this avoids race conditions when multiple agents run in parallel.

### Q&A agent sandbox

```bash
nono run \
  --read $VAULT \                          # full vault read — obsidian CLI search
  --allow-file $VAULT/queries/$SLUG \      # only if --save; pre-created by script
  -- claude --print "..." < qa-prompt.md
```

Same pattern: if `--save` is requested, the script pre-creates the target query file and grants `--allow-file` on that specific path.

### What the script does (no sandbox)

The user-controlled script runs outside any nono session and holds full filesystem access. It is responsible for:

- Pre-creating `_meta/review.md` if it does not exist
- Checking `_meta/review.md` for answered entries and computing `REVIEW_HAS_ANSWERS` before spawning agents
- Validating every path in the orchestrator JSON (must be within `$VAULT`, no traversal, correct content folder for the declared `type`)
- Pre-creating a staging subdirectory per file agent before spawning it
- Passing `REVIEW_HAS_ANSWERS` and the work plan entry in each agent's prompt context
- Reading all staging output files across all agent subdirectories and validating their frontmatter
- Moving staging output files to their declared `target` path (create or overwrite), stripping the `staging` block
- Appending all staged `_review.md` entries to `_meta/review.md`
- Updating `_meta/tags.md` with any new tags declared in staging frontmatter
- Removing successfully processed inbox files
- Cleaning up `inbox/staging/`

### Sandbox configuration

The vault path and tooling repo path are set once in a `.env` file (or exported shell variables) and referenced as `$VAULT` and `$TOOLING_REPO` in all nono invocations.

---

### Orchestrator agent

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

### File agent (one per inbox file)

**Responsibilities:**
- If `REVIEW_HAS_ANSWERS` is `true`: read `_meta/review.md`, act on any answered entries matching its inbox file, remove those entries from `review.md`
- Read the assigned inbox file
- Read all related vault files provided in the work plan entry
- Decide how to decompose the content: one inbox item may produce multiple output notes across different vault folders (e.g. an article that introduces a concept worth its own atomic note, triggers an update to an existing project note, and is itself archived in `articles/`)
- Write one staging file per output note to its assigned staging subdirectory
- If any question cannot be resolved without user input: write a `_review.md` file to the staging subdirectory with the question(s) — the script appends these to `_meta/review.md`

**Default behaviour: prefer decomposition.** If an inbox item touches multiple distinct topics, split it into atomic notes rather than cramming everything into one. Each atomic note should cover exactly one concept. Cross-link related output notes using `[[wikilinks]]` in the `links` field.

**What it does NOT do:** Write to vault content folders, write new entries directly to `_meta/review.md`, remove inbox files, or communicate with other file agents. It has no knowledge of other inbox items.

**Staging file format** — the agent writes one Markdown file per output note into its staging subdirectory. Each file has a `staging` block (instructions for the script) followed by standard note frontmatter and content:

```yaml
---
staging:
  action: create | update | drop | needs-review
  target: notes/some-note.md       # relative to $VAULT; required for create/update
  review_question: "..."           # only for needs-review
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

The `staging` block is consumed by the script and stripped before the file is written to the vault. For `update`, the agent writes the complete replacement content of the target note. For `drop`, the file body may be empty. For `needs-review`, the agent writes the content it would have created so the user can decide.

If the agent has questions for the user, it also writes a `_review.md` file to its staging subdirectory. Each question follows the format defined in the Review Queue Format section:

```markdown
- **[inbox/some-file.md | 2026-05-01]** Question text here?

  > Answer:

---
```

The script appends all `_review.md` entries to `_meta/review.md` after agents complete, in the same pass where it commits staging output files.

**Example decomposition** — a clipped article about a new database architecture might produce:
- `articles/distributed-sql-overview.md` (`action: create`) — the archived article itself
- `notes/consensus-algorithms.md` (`action: create`) — atomic note on a concept introduced in the article
- `notes/cap-theorem.md` (`action: update`) — existing note extended with new nuance from the article
- `projects/db-migration-2026.md` (`action: update`) — existing project note updated with a relevant reference

### Q&A agent

The Q&A workflow is a single agent — no sub-agents needed. One question maps to one bounded context: search, filter by summary, read relevant notes, answer. If the vault grows large enough that reading all relevant notes exceeds context, introduce a retrieval sub-agent that reads and scores notes, returning only the top N to the answering agent.

---

## Workflow 1: Inbox Processing (`ai inbox`)

**Trigger:** User runs `ai inbox` from the terminal.

**Inputs accepted into `inbox/`:**
- Files dropped manually (`.md`, `.txt`)
- Content clipped via Obsidian Web Clipper
- Files created by Claude from terminal paste or conversation

**Step 0 — Script pre-flight:**

- Creates `_meta/review.md` if it does not exist
- Reads `_meta/review.md` and computes `REVIEW_HAS_ANSWERS` (true if any entry has a non-empty `> Answer:` line)

**Step 1 — Orchestrator (script launches nono session):**

```bash
nono run --read $VAULT -- claude --print "..." < orchestrator-prompt.md
```

The orchestrator:
1. Reads all files in `inbox/` (excluding `inbox/staging/`)
2. For each file, reads its content and searches the vault for related topics
3. Reads the `summary` property of search results to assess relevance without loading full note content
4. Emits a JSON work plan to stdout (one entry per inbox file, listing related vault files)

The script captures stdout and validates every path in the JSON: must be within `$VAULT`, no path traversal, no unexpected locations.

**Step 2 — Script prepares staging:**

For each inbox file in the work plan, the script generates a unique agent ID and creates an empty subdirectory at `inbox/staging/$AGENT_ID/`. The agent ID is generated by the script, not the agent.

**Step 3 — File agents (script launches one nono session per inbox file, in parallel):**

```bash
nono run \
  --read $VAULT \
  --read-file $VAULT/inbox/$FILE \
  --allow $VAULT/inbox/staging/$AGENT_ID/ \
  --allow-file $VAULT/_meta/review.md \
  -- claude --print "..." < file-agent-prompt.md
```

The script injects `REVIEW_HAS_ANSWERS` and the work plan entry into each agent's prompt context before spawning.

Each file agent:
1. If `REVIEW_HAS_ANSWERS` is `true`: reads `_meta/review.md`, applies any answered entries for its inbox file, removes those entries
2. **Detects bare URLs** — if the inbox file contains only a URL, writes `_review.md` to staging with the question: "Bare URL — please clip with Obsidian Web Clipper and re-add as Markdown."
3. Reads the inbox file content
4. Reads all related vault files listed in its work plan entry
5. Decomposes the content into as many output notes as appropriate — atomic notes per concept, updates to existing notes, and the source article itself if worth archiving
6. Writes one staging file per output note into its subdirectory
7. If any question requires user input: writes `_review.md` to its staging subdirectory

**Step 4 — Script commits results:**

For each agent's staging subdirectory:
1. If a `_review.md` file is present: appends its entries to `_meta/review.md`
2. For each remaining staging output file:
   a. Reads and parses staging frontmatter
   b. Validates `target` path (within `$VAULT`, correct content folder for the declared `type`, no path traversal)
   c. Executes the action:
      - `create` → writes staging content to `target`, stripping the `staging` block (fails if target already exists)
      - `update` → overwrites `target` with staging content, stripping the `staging` block
      - `drop` → discards staging file silently
      - `needs-review` → content is already captured via `_review.md`; preserves inbox file
   d. Appends any `new_tags` to `_meta/tags.md`
3. Removes the inbox file once all its staging outputs are committed (skipped if the agent wrote a `_review.md` — the inbox file stays until the user answers and the next run resolves it)
4. Cleans up `inbox/staging/$AGENT_ID/`
5. Prints summary: N created, N updated, N dropped, N questions added to review

**Goal:** `inbox/` is empty after a run (except files flagged for review).

---

## Workflow 2: Q&A (`ai ask`)

**Trigger:** `ai ask "your question"` in terminal, or natural language question in a Claude conversation.

**Single agent — steps:**

1. Extract key terms and concepts from the question.
2. Run vault searches:
   ```
   obsidian search query="<term 1>" "<term 2>"
   ```
3. Read the `summary` property of each result to filter for relevance without loading full content.
4. Read the full content of the relevant notes only.
5. Compose an answer grounded in vault content.
6. Output:
   - The answer
   - A "Sources" section listing exact file paths and titles used

**Output:**
- Always printed to terminal.
- If `--save` flag is passed, also saved as `queries/YYYY-MM-DD-<slug>.md`.

---

## Technical Design

### This repo contains:
- `scripts/` — Bash or Python scripts for `ai inbox`, `ai ask`, etc.
- `prompts/` — System prompts and instruction files for Claude
- `.claude/` — Claude Code hooks and settings (already present)
- `specs/` — This spec and future specs
- `flake.nix` — Nix flake providing the reproducible dev shell

### Dependencies (all managed by Nix):

All runtime dependencies are declared in `flake.nix` and provided via `nix develop`. Nothing is installed globally or via pip/brew.

| Dependency | Purpose |
|---|---|
| `python3` | Script runtime |
| `obsidian-cli` | Vault search and property reads (already installed; pin version in flake) |

The flake provides a `devShell` that makes all tools available on `$PATH`. Scripts assume they are run inside `nix develop` (or via a wrapper that enters the shell automatically).

### Obsidian CLI:
Already installed. The CLI is the primary interface to the vault for search and property reads. Scripts wrap CLI calls and pass results to Claude.

### AI driver:
Claude Code (this repo's Claude instance) executes the workflows. For `ai inbox` and `ai ask`, Claude is called with the relevant vault data and a task-specific prompt.

### Script interface (proposed):
```bash
ai inbox              # Process all files in inbox/
ai inbox --dry-run    # Show what would happen without writing
ai ask "question"     # Q&A against the vault
ai ask "question" --save  # Q&A + save result as a note
```

---

## Edge Cases & Error Handling

| Scenario | Behavior |
|---|---|
| Inbox file has no discernible content | Leave in inbox, add to review.md with note "empty or unreadable" |
| New tag needed that doesn't exist | Create tag, add definition to `_meta/tags.md`, proceed |
| Obsidian CLI returns no search results | Still create the note; leave `links: []` empty |
| Inbox item overlaps with an existing note | Never duplicate. Compare content: if the inbox item adds new knowledge, append it to the existing note. If the inbox item adds nothing new, drop it silently. Never create a second note for the same concept. |
| Inbox item is a bare URL | Leave in inbox, add to review.md asking user to clip the page via Obsidian Web Clipper and re-add as Markdown. |
| `review.md` doesn't exist yet | Create it on first ambiguous case |
| Q&A finds no relevant notes | Return honest "no relevant notes found" — do not hallucinate |

---

## Open Questions

1. **Vault path** — Where is the Obsidian vault on disk? This must be configured (env var or config file) before any script can run.
2. **`ai` command entrypoint** — Is this a shell alias, a Python CLI, or a Bash script? Needs a decision before implementation starts.
3. **Obsidian CLI exact commands** — Need to verify the exact syntax of the installed CLI (search, property read) before writing wrapper scripts.
4. **Web Clipper output format** — What does Obsidian Web Clipper produce? If it already writes Markdown with frontmatter, the inbox processor may be able to reuse existing properties rather than regenerating them.
5. **Merge vs. append policy** — When should AI merge into an existing note vs. append a new linked note? Needs a concrete heuristic.
