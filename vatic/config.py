"""Configuration management for vatic.

Reads/writes ~/.config/vatic/config.toml (XDG-compliant).
"""

from pathlib import Path
import tomllib

try:
    import tomli_w as toml_write
except ImportError:
    toml_write = None


def get_config_dir() -> Path:
    """Get vatic config directory (~/.config/vatic)."""
    try:
        from platformdirs import user_config_dir
        return Path(user_config_dir("vatic"))
    except ImportError:
        # Fallback if platformdirs not available
        return Path.home() / ".config" / "vatic"


def get_config_path() -> Path:
    """Get vatic config file path."""
    return get_config_dir() / "config.toml"


def load_config() -> dict:
    """Load config from ~/.config/vatic/config.toml."""
    config_path = get_config_path()
    if not config_path.exists():
        return {}
    
    with open(config_path, 'rb') as f:
        return tomllib.load(f)


def save_config(config: dict) -> None:
    """Save config to ~/.config/vatic/config.toml."""
    if toml_write is None:
        raise RuntimeError("tomli-w is required to write config")

    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = get_config_path()
    with open(config_path, 'wb') as f:
        toml_write.dump(config, f)


def get_vault() -> Path | None:
    """Return configured vault path, or None if not set."""
    value = load_config().get("vault")
    return Path(value) if value else None


def get_tooling_repo() -> Path | None:
    """Return configured tooling repo path, or None if not set."""
    value = load_config().get("tooling_repo")
    return Path(value) if value else None


def set_value(key: str, value: str) -> None:
    """Set a config key to value and persist."""
    config = load_config()
    config[key] = value
    save_config(config)
