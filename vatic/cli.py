"""Command-line interface for vatic."""

import click


@click.group()
def main():
    """vatic — AI-driven vault editor for personal knowledge management."""
    pass


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
