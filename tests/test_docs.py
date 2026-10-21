"""The Python examples in the docs and the README.

Every example must compile. Examples marked ``<!-- test: run -->`` are complete programs: they run
against the devnet (``just test-devnet``), with their ``ws://localhost:1337`` pointed at it.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

import pytest

from .devnet import URL as DEVNET_URL

ROOT = Path(__file__).resolve().parents[1]
FENCE = re.compile(r"^(\s*)```(\w*)\s*$")
RUN_MARKER = "<!-- test: run -->"


@dataclass(frozen=True)
class Example:
    path: Path
    line: int
    code: str
    run: bool

    @property
    def id(self) -> str:
        return f"{self.path.relative_to(ROOT)}:{self.line}"


def examples() -> list[Example]:
    found = []
    for path in [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]:
        lines = path.read_text().splitlines()
        i = 0
        while i < len(lines):
            match = FENCE.match(lines[i])
            if match and match.group(2) == "python":
                start, indent = i, match.group(1)
                i += 1
                body = []
                while i < len(lines) and lines[i].strip() != "```":
                    body.append(lines[i])
                    i += 1
                previous = next(
                    (lines[j].strip() for j in range(start - 1, -1, -1) if lines[j].strip()), ""
                )
                code = textwrap.dedent("\n".join(line.removeprefix(indent) for line in body))
                found.append(Example(path, start + 1, code, previous == RUN_MARKER))
            i += 1
    return found


EXAMPLES = examples()


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda e: e.id)
def test_example_compiles(example: Example) -> None:
    # Fragments may use await at the top level, as in an asyncio REPL.
    compile(example.code, example.id, "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)


def test_there_are_runnable_examples() -> None:
    assert sum(example.run for example in EXAMPLES) >= 10


@pytest.mark.devnet
@pytest.mark.parametrize("example", [e for e in EXAMPLES if e.run], ids=lambda e: e.id)
def test_example_runs_against_the_devnet(example: Example) -> None:
    code = example.code.replace("ws://localhost:1337", DEVNET_URL)
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "PYTHONWARNINGS": "error::DeprecationWarning"},
        check=False,
    )
    if "Connect call failed" in result.stderr or "cannot connect" in result.stderr:
        pytest.skip(f"no devnet Ogmios at {DEVNET_URL}")
    assert result.returncode == 0, f"{example.id} failed:\n{result.stderr[-2000:]}"
