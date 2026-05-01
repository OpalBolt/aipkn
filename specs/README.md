# Specs

This directory contains the full specification for the AI-assisted knowledge base system. Read this index first, then follow the links relevant to your task.

## System in one paragraph

An `ai inbox` command processes files dropped into `vault/inbox/`. A user-controlled script drives the pipeline: it launches a read-only **orchestrator** agent that searches the vault and emits a JSON work plan, then launches one **file agent** per inbox item, each sandboxed to its own staging subdirectory. File agents decompose content into atomic notes and write proposed output to staging — they never touch the vault directly. The script validates and commits staging output to the vault, updates metadata, and surfaces any agent questions in `_meta/review.md` for the user to answer. A separate `ai ask` command runs a single read-only **Q&A agent** against the vault.

All agents run inside **nono sandboxes**. The AI never initiates a `nono run` — only the user-controlled script does.

---

## Spec files

| File | Contents |
|---|---|
| [overview.md](overview.md) | Problem, goals, non-goals |
| [data-model.md](data-model.md) | Vault folder structure, note frontmatter template, tag taxonomy, `review.md` format |
| [architecture.md](architecture.md) | Multi-agent diagram, security constraints, nono sandbox permissions per agent, script responsibilities |
| [agents.md](agents.md) | Orchestrator, file agent, and Q&A agent — responsibilities, output formats, staging file format, example decomposition |
| [workflows.md](workflows.md) | Step-by-step: `ai inbox` (Steps 0–4) and `ai ask` |
| [implementation.md](implementation.md) | Repo layout, dependencies, script interface, edge cases, open questions |

---

## Reading order for implementation

1. **[overview.md](overview.md)** — understand what we're building and what's out of scope
2. **[data-model.md](data-model.md)** — understand the vault layout and all file formats before touching anything else
3. **[architecture.md](architecture.md)** — understand the security model and what the script is responsible for
4. **[agents.md](agents.md)** — understand each agent's inputs, outputs, and constraints
5. **[workflows.md](workflows.md)** — understand the end-to-end sequence for each command
6. **[implementation.md](implementation.md)** — edge cases and open questions to resolve before writing code
