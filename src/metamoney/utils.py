import importlib.util
import pathlib
import sys
from types import ModuleType


def pascal_to_snake(pascal: str) -> str:
    snake = ""
    for i, char in enumerate(pascal):
        if ord(char) >= ord("A") and ord(char) <= ord("Z"):
            if i > 0:
                snake += "_"
            snake += char.lower()
            continue
        snake += char
    return snake


def get_config_module() -> ModuleType | None:
    spec = importlib.util.spec_from_file_location(
        "config", pathlib.Path.home() / ".metamoney" / "__init__.py"
    )
    if spec and spec.loader:
        config = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = config
        spec.loader.exec_module(config)
        return config
    return None
