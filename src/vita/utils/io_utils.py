import json
import os
import re
from pathlib import Path
from typing import Any

import toml
import yaml

# NOTE: When using the results of load_file(), we need to pay attention to the case
# where the value is None when loading from json or yaml, the key will be missing in
# toml since there is no "null" in toml.


def _substitute_env_vars(text: str) -> str:
    """Substitute environment variables in text using ${VAR:default} syntax.
    
    Args:
        text: The text to process
        
    Returns:
        Text with environment variables substituted
    """
    if not isinstance(text, str):
        return text
    
    # Pattern to match ${VAR:default} or ${VAR}
    pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
    
    def replace_var(match):
        var_name = match.group(1)
        default_value = match.group(2) if match.group(2) is not None else ""
        return os.getenv(var_name, default_value)
    
    return re.sub(pattern, replace_var, text)


def _recursive_substitute(data: Any) -> Any:
    """Recursively substitute environment variables in nested data structures.
    
    Args:
        data: The data structure to process
        
    Returns:
        Data with environment variables substituted
    """
    if isinstance(data, dict):
        return {key: _recursive_substitute(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_recursive_substitute(item) for item in data]
    elif isinstance(data, str):
        return _substitute_env_vars(data)
    else:
        return data


def load_file(path: str | Path, **kwargs: Any) -> dict[str, Any]:
    """Load the content of a file from a path based on the file extension.

    Args:
        path: The path to the file to load.
        **kwargs: Additional keyword arguments to pass to the file reader.

    Returns:
        The data dictionary loaded from the file.
    """
    path = Path(path)
    if path.suffix == ".json":
        with open(path, "r") as fp:
            data = json.load(fp, **kwargs)
    elif path.suffix == ".yaml" or path.suffix == ".yml":
        with open(path, "r") as fp:
            data = yaml.load(fp, Loader=yaml.SafeLoader, **kwargs)
        # Apply environment variable substitution for YAML files
        data = _recursive_substitute(data)
    elif path.suffix == ".toml":
        with open(path, "r") as fp:
            data = toml.load(fp, **kwargs)
    elif path.suffix == ".txt" or path.suffix == ".md":
        encoding = kwargs.pop("encoding", None)
        if len(kwargs) > 0:
            raise ValueError(f"Unsupported keyword arguments: {kwargs}")
        with open(path, "r", encoding=encoding) as fp:
            data = fp.read()
    else:
        raise ValueError(f"Unsupported file extension: {path}")
    return data


def dump_file(path: str | Path, data: dict[str, Any], **kwargs: Any) -> None:
    """Dump data content to a file based on the file extension.

    Args:
        path: The path to the file to dump the data to.
        data: The data dictionary to dump to the file.
        **kwargs: Additional keyword arguments to pass to the file writer.
    """
    path = Path(path)
    os.makedirs(path.parent, exist_ok=True)

    if path.suffix == ".json":
        with open(path, "w") as fp:
            json.dump(data, fp, ensure_ascii=False, **kwargs)
    elif path.suffix == ".yaml" or path.suffix == ".yml":
        with open(path, "w") as fp:
            yaml.dump(data, fp, **kwargs)
    elif path.suffix == ".toml":
        data_str = json.dumps(data, ensure_ascii=False)
        new_data = json.loads(data_str)
        with open(path, "w") as fp:
            toml.dump(new_data, fp, **kwargs)
    elif path.suffix == ".txt" or path.suffix == ".md":
        encoding = kwargs.pop("encoding", None)
        if len(kwargs) > 0:
            raise ValueError(f"Unsupported keyword arguments: {kwargs}")
        with open(path, "w", encoding=encoding) as fp:
            fp.write(data)
    else:
        raise ValueError(f"Unsupported file extension: {path}")
