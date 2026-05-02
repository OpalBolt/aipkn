"""Command-line interface for vatic."""

import click
from vatic.config import get_vault


_VAULT_DIRS = [
    "inbox",
    "inbox/staging",
    "notes",
    "articles",
    "projects",
    "tasks",
    "queries",
    "_meta",
    "_meta/templates",
]

_TAGS_MD = """\
# Tag Taxonomy

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

## Expansion policy
A file agent may introduce a new topic tag if no existing tag fits. It declares the tag and definition in the `new_tags` staging field. The `commit_staging` module appends new tags here — agents never write to this file directly.
"""

_REVIEW_MD = """\
# Review Queue

Items below require your input before they can be processed. Fill in the `> Answer:` line for each, then re-run `vatic inbox`.

---
"""

_NOTE_TEMPLATE_MD = """\
---
title:
date: YYYY-MM-DD
type: note
tags: []
summary:
source:
links: []
---

"""

_SEED_FILES = {
    "_meta/tags.md": _TAGS_MD,
    "_meta/review.md": _REVIEW_MD,
    "_meta/templates/note.md": _NOTE_TEMPLATE_MD,
}


@click.group()
def main():
    """vatic — AI-driven vault editor for personal knowledge management."""
    pass


@main.command()
def init():
    """Initialize the vault folder structure at the configured vault path."""
    vault = get_vault()
    if vault is None:
        raise click.ClickException(
            "Vault path not configured. "
            "Set 'vault = \"/path/to/vault\"' in ~/.config/vatic/config.toml"
        )

    vault = vault.resolve()

    for rel in _VAULT_DIRS:
        (vault / rel).mkdir(parents=True, exist_ok=True)

    created = 0
    for rel, content in _SEED_FILES.items():
        path = vault / rel
        if path.exists():
            click.echo(f"  skip   {rel} (already exists)")
        else:
            path.write_text(content, encoding="utf-8")
            click.echo(f"  create {rel}")
            created += 1

    if created:
        click.echo(f"\nVault initialized at {vault}")
    else:
        click.echo(f"\nVault already initialized at {vault}")


@main.command()
@click.option('--dry-run', is_flag=True, help='Show what would happen without writing')
def inbox(dry_run):
    """Process all files in inbox/."""
    click.echo(f"inbox command (dry_run={dry_run})")


@main.command()
@click.argument('question')
@click.option('--save', is_flag=True, help='Save result as a note')
def ask(question, save):
    """Q&A against the vault."""
    click.echo(f"ask: {question} (save={save})")


@main.group()
def config():
    """Manage vatic configuration."""
    pass


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Set a configuration value."""
    click.echo(f"vatic config set: not yet implemented")


if __name__ == "__main__":
    main()
