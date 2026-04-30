"""Loader module for loading env configs from files, directories, or mappings."""

from pathlib import Path
from typing import Dict, Optional, Union

from envdiff.parser import parse_env_file, parse_env_mapping, parse_env_string


class EnvSource:
    """Represents a named environment variable source."""

    def __init__(self, name: str, data: Dict[str, str]):
        self.name = name
        self.data = data

    def __repr__(self) -> str:
        return f"EnvSource(name={self.name!r}, keys={list(self.data.keys())})"

    def __len__(self) -> int:
        return len(self.data)


def load_from_file(path: Union[str, Path], name: Optional[str] = None) -> EnvSource:
    """Load an EnvSource from a .env file path."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Env file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    source_name = name or path.name
    data = parse_env_file(path)
    return EnvSource(name=source_name, data=data)


def load_from_string(content: str, name: str = "<string>") -> EnvSource:
    """Load an EnvSource from a raw env-format string."""
    data = parse_env_string(content)
    return EnvSource(name=name, data=data)


def load_from_mapping(mapping: Dict[str, str], name: str = "<mapping>") -> EnvSource:
    """Load an EnvSource from a plain dictionary."""
    data = parse_env_mapping(mapping)
    return EnvSource(name=name, data=data)


def load_from_directory(directory: Union[str, Path], pattern: str = "*.env") -> Dict[str, EnvSource]:
    """Load all matching env files from a directory, keyed by filename."""
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")
    sources = {}
    for path in sorted(directory.glob(pattern)):
        source = load_from_file(path)
        sources[path.name] = source
    return sources
