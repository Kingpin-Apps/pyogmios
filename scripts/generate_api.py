"""Generate ``api.py`` (a typed method per Ogmios query) and ``errors.py`` (an exception per failure code).

``client.ledger_state.<query>()`` and ``client.network.<query>()``, for the async and the sync client.
Keyword arguments come from the generated params models (when a query takes one of several param
shapes, their fields are merged into optional keywords), return types from the method table, and
docstrings from the schema's request descriptions.

``errors.py`` has one exception class per transaction submission and evaluation failure in the
schema, named after its title and documented with its description.

Run by scripts/generate.py after the models are generated.
"""

from __future__ import annotations

import json
import re
import sys
import types
import typing
from pathlib import Path
from typing import Any

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from pyogmios._generated import models  # noqa: E402
from pyogmios._generated.methods import METHODS, OGMIOS_VERSION  # noqa: E402

NAMESPACES = {
    "queryLedgerState/": (
        "LedgerStateQueries",
        "The ledger state queries (``queryLedgerState/*``).",
    ),
    "queryNetwork/": ("NetworkQueries", "The network queries (``queryNetwork/*``)."),
}


def snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def model_name(tp: Any) -> str | None:
    """``models.<Name>`` when ``tp`` is a generated model or alias."""
    name = getattr(tp, "__name__", None)
    if name and getattr(models, name, None) is tp:
        return f"models.{name}"
    return None


def render(tp: Any, *, accept_mappings: bool = False) -> str:
    """Python source for a type annotation.

    With ``accept_mappings``, every model also admits a plain mapping, as params are validated and
    plain dicts are accepted at runtime.
    """
    if tp is None or tp is type(None):
        return "None"
    if named := model_name(tp):
        if accept_mappings and isinstance(tp, type) and issubclass(tp, BaseModel):
            return f"{named} | Mapping[str, Any]"
        return named
    origin, args = typing.get_origin(tp), typing.get_args(tp)
    if origin is typing.Annotated:
        return render(args[0], accept_mappings=accept_mappings)
    if origin in (typing.Union, types.UnionType):
        return " | ".join(
            dict.fromkeys(render(arg, accept_mappings=accept_mappings) for arg in args)
        )
    if origin is typing.Literal:
        return f"Literal[{', '.join(repr(arg) for arg in args)}]"
    if origin in (list, dict, tuple, set):
        inner = ", ".join(render(arg, accept_mappings=accept_mappings) for arg in args)
        if accept_mappings and origin is list:
            return f"Sequence[{inner}]"  # any sequence works: params are validated
        return f"{origin.__name__}[{inner}]"
    if isinstance(tp, type) and tp.__module__ == "builtins":
        return tp.__name__
    return "Any"


def param_models(params: Any) -> list[type[BaseModel]]:
    """The params model, or each model of a union of param shapes."""
    value = getattr(params, "__value__", params)
    if isinstance(value, type) and issubclass(value, BaseModel):
        return [value]
    return [
        arg
        for arg in typing.get_args(value)
        if isinstance(arg, type) and issubclass(arg, BaseModel)
    ]


def keywords(spec: Any) -> list[tuple[str, str, bool, str]]:
    """``(name, annotation, required, description)`` for each keyword argument."""
    if spec.params is None:
        return []
    shapes = param_models(spec.params)
    merged: dict[str, tuple[str, bool, str]] = {}
    for shape in shapes:
        for name, field in shape.model_fields.items():
            annotation = render(field.annotation, accept_mappings=True)
            # A field is required only when the method has one param shape and the field needs a value.
            required = len(shapes) == 1 and spec.params_required and field.is_required()
            description = " ".join((field.description or "").replace("\u2019", "'").split())
            if name in merged:
                annotation = " | ".join(dict.fromkeys([merged[name][0], annotation]))
            merged[name] = (annotation, required, description)
    return [
        (name, annotation, required, description)
        for name, (annotation, required, description) in merged.items()
    ]


def signature(kws: list[tuple[str, str, bool, str]]) -> str:
    if not kws:
        return "self"
    parts = []
    for name, annotation, required, _ in sorted(kws, key=lambda kw: not kw[2]):
        if required:
            parts.append(f"{name}: {annotation}")
        else:
            optional = annotation if annotation.endswith("| None") else f"{annotation} | None"
            parts.append(f"{name}: {optional} = None")
    return "self, *, " + ", ".join(parts)


def docstring(description: str, kws: list[tuple[str, str, bool, str]], indent: str) -> list[str]:
    text = " ".join(description.replace("\u2019", "'").split()) or "Query Ogmios."
    lines = [f'{indent}"""{text}']
    documented = [kw for kw in kws if kw[3]]
    if documented:
        lines += ["", f"{indent}Args:"]
        lines += [f"{indent}    {name}: {desc}" for name, _, _, desc in documented]
    if len(lines) == 1:
        lines[0] += '"""'
    else:
        lines.append(f'{indent}"""')
    return lines


def call_args(method: str, kws: list[tuple[str, str, bool, str]]) -> str:
    if not kws:
        return f'"{method}"'
    pairs = ", ".join(f'"{name}": {name}' for name, *_ in kws)
    return f'"{method}", _params({{{pairs}}})'


def write_errors(ogmios: dict[str, Any]) -> None:
    """One exception class per submission and evaluation failure code."""
    import pyogmios.errors as handwritten

    # Only the hand-written classes: pyogmios.errors also re-exports the ones generated last time.
    taken = {
        name
        for name, value in vars(handwritten).items()
        if isinstance(value, type) and value.__module__ == "pyogmios.errors"
    }
    definitions = ogmios["definitions"]
    lines = [
        f'"""An exception for every transaction submission and evaluation failure in Ogmios v{OGMIOS_VERSION}.',
        "",
        "Generated by scripts/generate_api.py. Do not edit by hand: run `just regen-models`.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from ..errors import EvaluateTransactionError, SubmitTransactionError",
        "",
    ]
    tables: dict[str, list[tuple[int, str]]] = {}
    for definition, base, prefix in (
        ("EvaluateTransactionFailure", "EvaluateTransactionError", "Evaluate"),
        ("SubmitTransactionFailure", "SubmitTransactionError", "Submit"),
    ):
        table = tables.setdefault(definition, [])
        for branch in definitions[definition]["oneOf"]:
            if "$ref" in branch:
                branch = definitions[branch["$ref"].rsplit("/", 1)[1]]
            code = (
                branch["properties"]["code"].get("enum")
                or [branch["properties"]["code"].get("const")]
            )[0]
            short = re.search(r"<(\w+)>", branch["title"]).group(1)  # type: ignore[union-attr]
            name = short if short.endswith("Error") else f"{short}Error"
            if name in taken:
                name = f"{prefix}{name}"
            taken.add(name)
            description = " ".join(branch.get("description", "").replace("\u2019", "'").split())
            lines += [
                "",
                f"class {name}({base}):",
                f'    """{description + " " if description else ""}(code {code})"""',
                "",
                f"    codes = ({code},)",
                "",
            ]
            table.append((code, name))
    for definition, name, base in (
        ("SubmitTransactionFailure", "SUBMIT_ERRORS", "SubmitTransactionError"),
        ("EvaluateTransactionFailure", "EVALUATE_ERRORS", "EvaluateTransactionError"),
    ):
        lines += ["", f"{name}: dict[int, type[{base}]] = {{"]
        lines += [f"    {code}: {cls}," for code, cls in tables[definition]]
        lines += ["}"]
    names = [cls for table in tables.values() for _, cls in table]
    lines += [
        "",
        "__all__ = [",
        *[f'    "{n}",' for n in sorted([*names, "EVALUATE_ERRORS", "SUBMIT_ERRORS"])],
        "]",
        "",
    ]
    (ROOT / "src" / "pyogmios" / "_generated" / "errors.py").write_text("\n".join(lines))


def main() -> None:
    ogmios = json.loads((ROOT / "schemas" / f"v{OGMIOS_VERSION}" / "ogmios.json").read_text())
    descriptions = {
        name: schema.get("description", "") for name, schema in ogmios["properties"].items()
    }
    lines = [
        f'"""Typed methods for every Ogmios query, for Ogmios v{OGMIOS_VERSION}.',
        "",
        "Generated by scripts/generate_api.py. Do not edit by hand: run `just regen-models`.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from collections.abc import Awaitable, Callable, Mapping, Sequence",
        "from typing import TYPE_CHECKING, Any, Literal, TypeVar",
        "",
        "from . import models",
        "",
        "if TYPE_CHECKING:",
        "    from ..client import AsyncClient",
        "",
        'T = TypeVar("T")',
        "",
        "",
        "def _params(values: dict[str, Any]) -> dict[str, Any] | None:",
        '    """The keyword arguments that were given, or ``None`` when none were."""',
        "    given = {name: value for name, value in values.items() if value is not None}",
        "    return given or None",
        "",
    ]
    for prefix, (class_name, class_doc) in NAMESPACES.items():
        queries = [(name, spec) for name, spec in METHODS.items() if name.startswith(prefix)]
        # Async namespace.
        lines += ["", f"class Async{class_name}:", f'    """{class_doc}"""', ""]
        lines += [
            "    def __init__(self, client: AsyncClient) -> None:",
            "        self._client = client",
            "",
        ]
        for name, spec in queries:
            kws = keywords(spec)
            result = model_name(spec.result) or "Any"
            lines.append(
                f"    async def {snake(name.split('/', 1)[1])}({signature(kws)}) -> {result}:"
            )
            lines += docstring(descriptions.get(spec.schema_name, ""), kws, "        ")
            lines += [f"        return await self._client.call({call_args(name, kws)})", ""]
        # Sync namespace, delegating to the async one through the client's event loop.
        lines += ["", f"class {class_name}:", f'    """{class_doc}"""', ""]
        lines += [
            f"    def __init__(self, queries: Async{class_name}, run: Callable[[Awaitable[Any]], Any]) -> None:",
            "        self._queries = queries",
            "        self._run = run",
            "",
        ]
        for name, spec in queries:
            kws = keywords(spec)
            method = snake(name.split("/", 1)[1])
            result = model_name(spec.result) or "Any"
            forward = ", ".join(f"{kw[0]}={kw[0]}" for kw in kws)
            lines.append(f"    def {method}({signature(kws)}) -> {result}:")
            lines += docstring(descriptions.get(spec.schema_name, ""), kws, "        ")
            lines += [f"        return self._run(self._queries.{method}({forward}))", ""]
    lines.append("")
    (ROOT / "src" / "pyogmios" / "_generated" / "api.py").write_text("\n".join(lines))
    write_errors(ogmios)


if __name__ == "__main__":
    main()
