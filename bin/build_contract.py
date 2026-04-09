#!/usr/bin/env python3
"""
Generate contract.json — a machine-readable description of the PropWeaver public API.

Intended for consumption by AI agents (e.g. Claude Code) working on projects that
import propweaver, so they can verify method names, signatures, and return types
without reading source code.

Usage:
    uv run python bin/build_contract.py
    # writes contract.json to the repo root
"""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path
from typing import Any, get_type_hints

# Ensure the src layout is importable when run directly
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import propweaver
from propweaver import (
    PropertyGraph,
    NodeProxy,
    EdgeProxy,
    NodeIterator,
    EdgeIterator,
    QuerySpec,
    QueryStep,
)
from propweaver import exceptions as exc_module
import propweaver.exceptions as _exc


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _annotation_str(annotation: Any) -> str:
    """Convert a type annotation to a readable string."""
    if annotation is inspect.Parameter.empty or annotation is inspect.Signature.empty:
        return "Any"
    if hasattr(annotation, "__name__"):
        return annotation.__name__
    return str(annotation).replace("typing.", "").replace("propweaver.core.", "")


def _describe_method(method: Any) -> dict:
    """Describe a single method: params, return type, docstring."""
    try:
        sig = inspect.signature(method)
    except (ValueError, TypeError):
        return {"description": inspect.getdoc(method) or ""}

    params = {}
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        entry: dict[str, Any] = {"type": _annotation_str(param.annotation)}
        if param.default is not inspect.Parameter.empty:
            try:
                json.dumps(param.default)  # only include JSON-serialisable defaults
                entry["default"] = param.default
            except (TypeError, ValueError):
                entry["default"] = repr(param.default)
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            entry["kind"] = "**kwargs"
        elif param.kind == inspect.Parameter.VAR_POSITIONAL:
            entry["kind"] = "*args"
        params[name] = entry

    return {
        "params": params,
        "returns": _annotation_str(sig.return_annotation),
        "description": inspect.getdoc(method) or "",
    }


def _describe_class(cls: type, public_methods: list[str] | None = None) -> dict:
    """Describe a class: constructor, methods, properties, docstring."""
    result: dict[str, Any] = {
        "description": inspect.getdoc(cls) or "",
        "constructor": _describe_method(cls.__init__),
    }

    methods: dict[str, Any] = {}
    properties: dict[str, Any] = {}

    names = public_methods if public_methods is not None else [
        name for name in dir(cls)
        if not name.startswith("_") or name in ("__repr__", "__enter__", "__exit__", "__iter__")
    ]

    for name in sorted(names):
        obj = getattr(cls, name, None)
        if obj is None:
            continue
        if isinstance(obj, property):
            properties[name] = {
                "type": _annotation_str(
                    get_type_hints(obj.fget).get("return", inspect.Parameter.empty)
                    if obj.fget else inspect.Parameter.empty
                ),
                "description": inspect.getdoc(obj) or "",
            }
        elif callable(obj) and not name.startswith("_"):
            methods[name] = _describe_method(obj)

    if properties:
        result["properties"] = properties
    if methods:
        result["methods"] = methods

    return result


# ─── Build contract ───────────────────────────────────────────────────────────


def build() -> dict:
    contract: dict[str, Any] = {
        "propweaver_version": propweaver.__version__,
        "description": (
            "Machine-readable PropWeaver public API contract. "
            "Use this file to verify method names, parameter types, and return types "
            "before calling PropWeaver from another project."
        ),
    }

    # ── Core classes ──────────────────────────────────────────────────────────
    contract["classes"] = {
        "PropertyGraph": {
            "import": "from propweaver import PropertyGraph",
            "alias": "Graph",
            **_describe_class(PropertyGraph),
        },
        "NodeProxy": {
            "import": "from propweaver import NodeProxy",
            "note": "Returned by PropertyGraph.add_node() and node iterators. Not instantiated directly.",
            **_describe_class(NodeProxy),
        },
        "EdgeProxy": {
            "import": "from propweaver import EdgeProxy",
            "note": "Returned by PropertyGraph.add_edge() and edge iterators. Not instantiated directly.",
            **_describe_class(EdgeProxy),
        },
        "NodeIterator": {
            "import": "from propweaver import NodeIterator",
            "note": "Returned by PropertyGraph.nodes(). Supports method chaining and iteration.",
            **_describe_class(NodeIterator),
        },
        "EdgeIterator": {
            "import": "from propweaver import EdgeIterator",
            "note": "Returned by PropertyGraph.edges(). Supports method chaining and iteration.",
            **_describe_class(EdgeIterator),
        },
    }

    # ── Query dataclasses ─────────────────────────────────────────────────────
    contract["query"] = {
        "description": (
            "Declarative query representation. Advanced use only — "
            "most callers use the fluent API on NodeIterator/EdgeIterator instead."
        ),
        "QueryStep": {
            "import": "from propweaver import QueryStep",
            "fields": {
                "type": {
                    "type": "Literal['SOURCE', 'FILTER', 'TRAVERSE', 'ORDER', 'DELETE']",
                    "description": "Operation type",
                },
                "target": {
                    "type": "Optional[str]",
                    "default": None,
                    "description": "For SOURCE: 'all_nodes' or 'all_edges'",
                },
                "node_type": {"type": "Optional[str]", "default": None},
                "edge_type": {"type": "Optional[str]", "default": None},
                "properties": {"type": "Optional[dict]", "default": None},
                "direction": {
                    "type": "Literal['out', 'in', 'both']",
                    "default": "both",
                    "description": "For TRAVERSE steps",
                },
                "field": {"type": "Optional[str]", "default": None, "description": "For ORDER steps"},
                "order": {
                    "type": "Optional[Literal['asc', 'desc']]",
                    "default": None,
                    "description": "For ORDER steps",
                },
            },
        },
        "QuerySpec": {
            "import": "from propweaver import QuerySpec",
            "fields": {
                "steps": {"type": "List[QueryStep]", "default": []},
                "returning": {
                    "type": "Literal['nodes', 'edges', 'target_nodes', 'source_nodes']",
                    "default": "nodes",
                },
                "limit": {"type": "Optional[int]", "default": None},
            },
        },
    }

    # ── Property value types ──────────────────────────────────────────────────
    contract["property_types"] = {
        "description": "Python types that may be stored as node/edge/graph property values.",
        "supported": ["str", "int", "float", "bool", "datetime", "date", "list", "dict"],
        "unsupported": ["None  # raises PropertyValueError"],
        "storage_types": ["str", "int", "float", "bool", "datetime", "date", "json"],
    }

    # ── Exceptions ────────────────────────────────────────────────────────────
    exc_classes: dict[str, Any] = {}
    for name in sorted(dir(_exc)):
        obj = getattr(_exc, name)
        if (
            isinstance(obj, type)
            and issubclass(obj, Exception)
            and obj.__module__ == "propweaver.exceptions"
        ):
            bases = [b.__name__ for b in obj.__bases__ if b is not Exception]
            entry: dict[str, Any] = {"description": inspect.getdoc(obj) or ""}
            if bases:
                entry["inherits"] = bases
            exc_classes[name] = entry

    contract["exceptions"] = {
        "import": "from propweaver import <ExceptionClass>",
        "hierarchy_root": "PropWeaverError",
        "classes": exc_classes,
    }

    # ── Pydantic API models ───────────────────────────────────────────────────
    try:
        from propweaver import api as api_module
        from pydantic import BaseModel

        models: dict[str, Any] = {}
        for name in sorted(dir(api_module)):
            obj = getattr(api_module, name)
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseModel)
                and obj.__module__ == "propweaver.api"
            ):
                schema = obj.model_json_schema()
                models[name] = {
                    "import": f"from propweaver.api import {name}",
                    "description": inspect.getdoc(obj) or "",
                    "json_schema": schema,
                }

        contract["api_models"] = {
            "description": (
                "Pydantic v2 models for validating PropWeaver return values. "
                "Requires: pip install 'propweaver[api]'"
            ),
            "models": models,
        }
    except ImportError:
        contract["api_models"] = {
            "description": "Pydantic models not available. Install with: pip install 'propweaver[api]'",
            "models": {},
        }

    return contract


# ─── Entry point ──────────────────────────────────────────────────────────────


def main() -> None:
    repo_root = Path(__file__).parent.parent
    out_path = repo_root / "contract.json"

    contract = build()
    out_path.write_text(json.dumps(contract, indent=2, default=str))
    print(f"✅ contract.json written ({out_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
