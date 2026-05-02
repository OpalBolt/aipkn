"""Pre-flight screening for inbox items.

Detects bare URLs and empty inbox files before spawning agents.
"""


def is_bare_url(content: str) -> bool:
    """Check if content is a bare URL."""
    content = content.strip()
    return content.startswith('http://') or content.startswith('https://')


def is_empty_or_unreadable(content: str) -> bool:
    """Check if content is empty or unreadable."""
    return not content or not content.strip()
