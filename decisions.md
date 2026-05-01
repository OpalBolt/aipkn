# Pre-Implementation Decisions — Issue #1

This document records architectural decisions made before implementation begins. Each decision resolves a blocker for downstream issues.

---

## Decision 1: Vault Path Configuration

**Question:** How is $VAULT set?

**Options Considered:**
- .env file in the tooling repo (simplest, already mentioned in specs)
- Exported shell variable only
- A small vatic config command that writes it

**Decision: .env file (recommended)**

Every script and entrypoint will source .env at the top. This provides:
- Centralized configuration in one file
- Easy to reference and update
- No manual shell exports needed
- Clear separation between config and code

**Implementation:**
- .env.example exists with VAULT= and TOOLING_REPO= placeholders
- .env is added to .gitignore (never committed)
- All scripts source it: source "$(dirname "$0")/../.env"

**Rationale:** Simplest approach that works for local development and tooling without requiring external config systems.

---

## Decision 2: vatic Entrypoint Type

**Question:** Shell alias, Bash script, or Python CLI (argparse)?

**Options Considered:**
- Shell alias (minimal)
- Bash script (simple, readable)
- Python CLI with argparse (extensible, but adds dependency)

**Decision: Single Bash script at scripts/vatic**

A single entry point at scripts/vatic will be added to $PATH via nix develop. This provides:
- No extra runtime dependencies
- Easy to read and debug
- Simple to extend with shell functions
- Works seamlessly with existing shell ecosystem

**Implementation:**
- Location: scripts/vatic
- Added to $PATH via nix develop environment
- Dispatches to sub-commands (e.g., vatic inbox, vatic ask) as Bash functions

**Rationale:** Keeps tooling lightweight and maintainable while remaining flexible for future growth.

---

## Decision 3: Obsidian CLI Exact Syntax

**Question:** Are the assumed Obsidian CLI commands correct?

**Assumed Commands:**
obsidian search query="term"
obsidian property:read file="path/to/file.md" name=description

**Decision: Assumed correct — verify before first use**

The commands match the syntax recorded in DESIGN.md. They have not been run against a live Obsidian CLI instance yet. Before writing any wrapper or agent prompt that calls them, the implementer must:
- Confirm the installed Obsidian CLI version supports these sub-commands
- Confirm output format (JSON vs plain text) for each command
- Add error handling for missing files or properties

**Implementation:**
- Scripts will wrap these commands with error checking
- Agent prompts will include syntax notes for operators
- First-use verification should be noted in the implementing PR

**Rationale:** Recording the assumed syntax now prevents divergence; requiring explicit verification before first use prevents silent breakage.

---

## Decision 4: Web Clipper Output Format

**Question:** Does Obsidian Web Clipper already write YAML frontmatter?

**Decision: Reuse existing frontmatter fields**

The Obsidian Web Clipper already writes YAML frontmatter with fields:
- title (page title)
- source (original URL)
- date (capture date)

The editor agent can reuse these fields rather than regenerating them. The note template should reflect this to avoid duplication.

**Implementation:**
- Editor agent reads frontmatter without modification
- Note template includes conditional sections based on existing fields
- Only add additional frontmatter (e.g., custom tags) if not already present

**Rationale:** Preserves metadata quality and avoids overwriting user-customized fields from Web Clipper.

---

## Decision 5: Merge vs. Append Heuristic

**Question:** When an inbox item overlaps with an existing note, should it be merged or appended?

**Decision: Use content-based heuristic**

When the editor agent encounters an inbox item that relates to an existing note, it will:

1. **Merge (update existing note)** if the inbox item:
   - Extends an existing concept (adds examples, clarifications, nuance)
   - Corrects or improves existing content
   - Fills gaps in explanation or structure

2. **Create new linked note** if the inbox item:
   - Introduces a related but distinct concept
   - Deserves independent atomic structure
   - Would fragment the existing note if merged

3. **Drop** if the inbox item:
   - Adds nothing new
   - Is a duplicate of existing content
   - Is tangentially related but not actionable

**Implementation:**
- Agent prompt includes this heuristic as decision logic
- Editor logs decisions in commit messages for transparency
- Regular review of merged vs. created notes to refine heuristic

**Rationale:** Provides clear guidance to the editor agent without over-constraining decisions, enabling both consolidation and atomic note creation as appropriate.

---

## Sign-Off

All five pre-implementation decisions are now recorded and actionable. The following issues can now proceed with implementation:
- Issue #2: Repo scaffold and dev environment (flake.nix)
- Issues #3–#12: Architecture implementation and integration tests

**Date Recorded:** 2026-05-01
