# Implementation Notes

> Related specs: [architecture](architecture.md) · [workflows](workflows.md) · [agents](agents.md)

---

## Technical Design

### This repo contains

- `vatic/` — Python package (entry point + modules)
  - `__main__.py` / `cli.py` — Click/Typer CLI; subcommands `inbox`, `ask`, `config`
  - `pre_screen.py` — detects bare URLs and empty inbox files before spawning agents
  - `check_review.py` — parses `_meta/review.md`, checks which entries are answered
  - `commit_staging.py` — validates and commits staging output to vault after agents complete
  - `config.py` — reads/writes `~/.config/vatic/config.toml` (XDG)
- `pyproject.toml` — package definition; declares `vatic` as a `[project.scripts]` entry point
- `.claude/agents/` — Agent definition files (one per agent) in Claude Code sub-agent format; frontmatter defines `model`, `effort`, `tools`, and `maxTurns`
- `.claude/` — Claude Code hooks and settings (already present)
- `specs/` — Spec files
- `flake.nix` — Nix flake providing the reproducible dev shell

### Dependencies (all managed by Nix)

All runtime dependencies are declared in `flake.nix` and provided via `nix develop`. Nothing is installed globally or via pip/brew.

| Dependency | Purpose |
|---|---|
| `python3` | CLI runtime |
| `click` or `typer` | CLI framework for `vatic` entry point and subcommands |
| `platformdirs` | XDG-compliant config directory resolution (`~/.config/vatic/`) |
| `tomllib` / `tomli` | Config file parsing (stdlib in Python 3.11+) |
| `obsidian-cli` | Vault search and property reads (already installed; pin version in flake) |

The flake provides a `devShell` that makes all tools available on `$PATH`. Scripts assume they are run inside `nix develop` (or via a wrapper that enters the shell automatically).

### Obsidian CLI

Already installed. The CLI is the primary interface to the vault for search and property reads. Scripts wrap CLI calls and pass results to Claude.

### AI driver

Claude Code executes the workflows. For `vatic inbox` and `vatic ask`, Claude is called with the relevant vault data and a task-specific prompt via `--print` mode (non-interactive).

### Script interface

```bash
vatic inbox              # Process all files in inbox/
vatic inbox --dry-run    # Show what would happen without writing
vatic ask "question"     # Q&A against the vault
vatic ask "question" --save  # Q&A + save result as a note
```

---

## Edge Cases & Error Handling

| Scenario | Behavior |
|---|---|
| Inbox file has no discernible content | Write `_review.md` to staging: "empty or unreadable" |
| New tag needed that doesn't exist | Declare in staging `new_tags`; script appends to `_meta/tags.md` |
| Obsidian CLI returns no search results | Still create the note; leave `links: []` empty |
| Inbox item overlaps with an existing note | See merge heuristic in Decisions §5. Options are `update` (append or correct), `create` (new sister note, cross-linked), or `drop` (1:1 overlap). Never create a duplicate of an existing concept. |
| Inbox item is a bare URL | Write `_review.md` to staging asking user to clip via Obsidian Web Clipper and re-add as Markdown. Inbox file stays. |
| `review.md` doesn't exist yet | Script pre-creates it during pre-flight (Step 0) |
| Staging `create` target already exists | Script fails with an error — orchestrator should have surfaced the existing file as a related file |
| Q&A finds no relevant notes | Return honest "no relevant notes found" — do not hallucinate |

---

## Decisions

### 1. Vault path configuration

Configuration lives in `~/.config/vatic/config.toml` (XDG_CONFIG_HOME). This is user-level config, not repo-level — `vatic` is a tool you run from anywhere, so tying config to a `.env` file in the tooling repo is the wrong scope. The config file is created and updated via `vatic config set vault <path>` and `vatic config set tooling-repo <path>`. No `.env` file; no manual sourcing.

### 2. `vatic` entrypoint type

`vatic` is a **Python CLI** package (`pyproject.toml` + Click or Typer), with `vatic` declared as a `[project.scripts]` entry point. Nix exposes it via `nix develop`. The Python helpers (`pre-screen.py`, `check-review.py`, `commit-staging.py`) become modules within the same package — no Bash/Python split. One language, one entry point, one package.

### 3. Obsidian CLI syntax

The following syntax is confirmed correct against the installed version:

```sh
obsidian search query="term"
obsidian property:read file="path/to/file.md" name=description
```

### 4. Web Clipper output format and handling

Obsidian Web Clipper writes `.md` files with YAML frontmatter (including `title`, `source`, `date`). When a clipped file lands in `inbox/`, the editor agent treats it as any other inbox item — it decomposes the content into atomic notes rather than archiving the clipped file as-is. The existing frontmatter fields (`source`, `date`) should be propagated to the atomic notes it creates (e.g., as the `source` property) so provenance is preserved.

### 5. Merge vs. append heuristic

When an inbox item overlaps with an existing vault note, the editor agent decides the action based on the nature of the overlap:

| Situation | Action |
|-----------|--------|
| Inbox item *adds* to an existing concept (new examples, new sections, additional data) | `update` — append the new content to the existing note |
| Inbox item *corrects or replaces* existing content in a note | `update` — edit the affected sections |
| Inbox item introduces a *related but distinct* concept | `create` — new atomic note, cross-linked to the existing one |
| Inbox item overlaps 1:1 with an existing note (nothing new) | `drop` |

The `update` action covers both append-style additions and in-place corrections — the agent writes the full merged content to the staging file. The script then overwrites the target file with the merged result.
