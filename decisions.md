# Pre-implementation Decisions

Fill in your answers below each question. Leave the recommendation note for reference.

---

## 1. Vault path configuration

How should `$VAULT` (and `$TOOLING_REPO`) be set?

**Options:**

- `.env` file in the tooling repo (sourced by every script/entrypoint)
- Exported shell variable only (set in `~/.zshrc` / `~/.bashrc`)
- A `vatic config` command that writes the value somewhere

**Recommendation:** `.env` file with `VAULT=` and `TOOLING_REPO=` — source it at the top of every script. Add `.env.example`; add `.env` to `.gitignore`.

**Your decision:** XDG config (`~/.config/vatic/config.toml`) managed via `vatic config set`. No `.env` file — config is user-level, not repo-level.

---

## 2. `vatic` entrypoint type

What form should the `vatic` CLI take?

**Options:**

- Shell alias (defined in `.zshrc` / shell init)
- Bash script at `scripts/vatic`, added to `$PATH` via `nix develop`
- Python CLI using `argparse` (or Click/Typer)

**Recommendation:** Single Bash script — simple, no extra deps, easy to read.

**Your decision:** Python CLI package (`pyproject.toml` + Click or Typer). The helpers become modules in the same package. No Bash entrypoint. Config via XDG (decision #1) makes Bash sourcing unnecessary anyway.

---

## 3. Obsidian CLI exact syntax

The specs assume the following CLI syntax. Verify these are correct against the installed version before writing any wrapper or agent prompt that calls them.

```sh
obsidian search query="term"
obsidian property:read file="path/to/file.md" name=description
```

**Steps to verify:**

1. Run `obsidian --help` (or `obsidian help`)
2. Test `obsidian search query="test"` against your vault
3. Test `obsidian property:read` against a known file

**Your answer** (paste confirmed syntax, or note corrections): This is correct and working queries

---

## 4. Web Clipper output format

Does Obsidian Web Clipper already write YAML frontmatter to clipped notes?

If **yes**, the editor agent can reuse existing fields (`title`, `source`, `date`) rather than regenerating them, and the note template should reflect that.

If **no**, the editor agent must extract and write those fields itself.

**Check:** Open a note clipped by Web Clipper and look at its raw Markdown for a `---` frontmatter block.

**Your answer** (yes/no, and which fields are present if yes): The yaml web clipper makes notes in .md format. I do not want to just store the content of the web-clipper, i want to extract important atomic notes from it.

---

## 5. Merge vs. append heuristic

When an inbox item overlaps with an existing vault note, should the editor agent merge into the existing note or create a new linked note?

**Draft heuristic (adjust as needed):**

| Situation | Action |
|-----------|--------|
| Inbox item *extends* an existing concept (adds examples, corrects info, adds nuance) | `update` the existing note |
| Inbox item introduces a *related but distinct* concept | `create` a new atomic note and cross-link |
| Inbox item adds nothing new | `drop` |

**Your decision** (accept the draft heuristic, or describe your preferred rules): This really depends on the note in question. Sometimes the correct answer is to append more data to the note. Sometimes its to update the existing data in the note, some times it to create a new "sister note" and some time if the data overlaps 1:1 to drop the new notes

---

*Once all five answers are filled in, use them to update `specs/implementation.md` and close issue #1.*
