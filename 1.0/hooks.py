"""MkDocs hooks: tables generated from the code, so the docs cannot drift from it.

- ``<!-- queries:table -->``: every query, with its Ogmios method, Python method, result and description.
- ``<!-- errors:table -->``: every exception chosen by an Ogmios error code.
- ``<!-- cli:help -->``: the command line's ``--help``.
"""

from __future__ import annotations

import inspect
import io
import re
from contextlib import redirect_stdout
from typing import Any

from pyogmios import errors
from pyogmios._generated.api import AsyncLedgerStateQueries, AsyncNetworkQueries
from pyogmios._generated.methods import METHODS
from pyogmios.cli import build_parser


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _summary(text: str | None) -> str:
    """The first paragraph of a docstring, on one line."""
    paragraph = inspect.cleandoc(text or "").split("\n\n", 1)[0]
    return " ".join(paragraph.split()).replace("|", "\\|")


def _type_name(tp: Any) -> str:
    return getattr(tp, "__name__", str(tp))


def queries_table() -> str:
    rows = ["| Ogmios method | Python | Result | Description |", "|---|---|---|---|"]
    for method, spec in METHODS.items():
        namespace, _, name = method.partition("/")
        if namespace not in ("queryLedgerState", "queryNetwork"):
            continue
        attribute = "ledger_state" if namespace == "queryLedgerState" else "network"
        queries = AsyncLedgerStateQueries if attribute == "ledger_state" else AsyncNetworkQueries
        function = getattr(queries, _snake(name))
        parameters = [p for p in inspect.signature(function).parameters if p != "self"]
        call = f"client.{attribute}.{_snake(name)}({', '.join(f'{p}=…' for p in parameters)})"
        rows.append(
            f"| `{method}` | `{call}` | `{_type_name(spec.result)}` | {_summary(function.__doc__)} |"
        )
    return "\n".join(rows)


def errors_table() -> str:
    classes = [
        cls
        for cls in vars(errors).values()
        if isinstance(cls, type) and issubclass(cls, errors.ResponseError) and cls.codes
    ]
    classes.sort(key=lambda cls: (cls.codes[0] < 0, abs(cls.codes[0])))
    rows = ["| Code | Exception | Parent | Meaning |", "|---|---|---|---|"]
    for cls in classes:
        doc = _summary(cls.__doc__).removesuffix(f" (code {cls.codes[0]})")
        rows.append(f"| {cls.codes[0]} | `{cls.__name__}` | `{cls.__mro__[1].__name__}` | {doc} |")
    return "\n".join(rows)


def cli_help() -> str:
    parser = build_parser()
    out = io.StringIO()
    with redirect_stdout(out):
        parser.print_help()
    return f"```text\n{out.getvalue().rstrip()}\n```"


GENERATED = {
    "<!-- queries:table -->": queries_table,
    "<!-- errors:table -->": errors_table,
    "<!-- cli:help -->": cli_help,
}


def on_page_markdown(markdown: str, **kwargs: Any) -> str:
    for placeholder, generate in GENERATED.items():
        if placeholder in markdown:
            markdown = markdown.replace(placeholder, generate())
    return markdown
