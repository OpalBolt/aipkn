# Implementation Notes

> Related specs: [architecture](architecture.md) · [workflows](workflows.md) · [agents](agents.md)

---

## Technical Design

### This repo contains

- `scripts/` — Bash or Python scripts for `ai inbox`, `ai ask`, etc.
- `prompts/` — System prompts and instruction files for Claude
- `.claude/` — Claude Code hooks and settings (already present)
- `specs/` — Spec files
- `flake.nix` — Nix flake providing the reproducible dev shell

### Dependencies (all managed by Nix)

All runtime dependencies are declared in `flake.nix` and provided via `nix develop`. Nothing is installed globally or via pip/brew.

| Dependency | Purpose |
|---|---|
| `python3` | Script runtime |
| `obsidian-cli` | Vault search and property reads (already installed; pin version in flake) |

The flake provides a `devShell` that makes all tools available on `$PATH`. Scripts assume they are run inside `nix develop` (or via a wrapper that enters the shell automatically).

### Obsidian CLI

Already installed. The CLI is the primary interface to the vault for search and property reads. Scripts wrap CLI calls and pass results to Claude.

### AI driver

Claude Code executes the workflows. For `ai inbox` and `ai ask`, Claude is called with the relevant vault data and a task-specific prompt via `--print` mode (non-interactive).

### Script interface

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
| Inbox file has no discernible content | Write `_review.md` to staging: "empty or unreadable" |
| New tag needed that doesn't exist | Declare in staging `new_tags`; script appends to `_meta/tags.md` |
| Obsidian CLI returns no search results | Still create the note; leave `links: []` empty |
| Inbox item overlaps with an existing note | Never duplicate. If the inbox item adds new knowledge, update the existing note. If it adds nothing new, drop it silently. Never create a second note for the same concept. |
| Inbox item is a bare URL | Write `_review.md` to staging asking user to clip via Obsidian Web Clipper and re-add as Markdown. Inbox file stays. |
| `review.md` doesn't exist yet | Script pre-creates it during pre-flight (Step 0) |
| Staging `create` target already exists | Script fails with an error — orchestrator should have surfaced the existing file as a related file |
| Q&A finds no relevant notes | Return honest "no relevant notes found" — do not hallucinate |

---

## Open Questions

1. **Vault path** — Where is the Obsidian vault on disk? This must be configured (env var or config file) before any script can run.
2. **`ai` command entrypoint** — Is this a shell alias, a Python CLI, or a Bash script? Needs a decision before implementation starts.
3. **Obsidian CLI exact commands** — Need to verify the exact syntax of the installed CLI (search, property read) before writing wrapper scripts.
4. **Web Clipper output format** — What does Obsidian Web Clipper produce? If it already writes Markdown with frontmatter, the inbox processor may be able to reuse existing properties rather than regenerating them.
5. **Merge vs. append policy** — When should AI merge into an existing note vs. append a new linked note? Needs a concrete heuristic.
