from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    schema: dict
    handler: Callable[[dict], Any]


TOOLS: dict[str, Tool] = {}


def schema(required: tuple[str, ...] | list[str] = (), **props: dict) -> dict:
    return {"type": "object", "required": list(required), "properties": props}


def tool(name: str, description: str, input_schema: dict):
    def decorate(function: Callable[[dict], Any]):
        if name in TOOLS:
            raise RuntimeError(f"duplicate tool {name}")
        TOOLS[name] = Tool(name, description, input_schema, function)
        return function
    return decorate


STR = {"type": "string"}
INT = {"type": "integer"}
BOOL = {"type": "boolean"}
