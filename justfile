# pyogmios development tasks. Run `just` to list them.

pythons := "3.11 3.12 3.13 3.14 3.15"
free_threaded := "3.14t 3.15t"
ogmios_url := env("OGMIOS_URL", "ws://localhost:1337")

default:
    @just --list

# Install the project and all development groups
sync:
    uv sync --all-groups

# Run the unit tests on the default Python
test *args:
    uv run pytest -m "not integration" {{args}}

# Run the unit tests on every supported Python, each in its own environment
test-all *args:
    #!/usr/bin/env bash
    set -uo pipefail
    failed=()
    for py in {{pythons}}; do
        echo "==> Python $py"
        UV_PROJECT_ENVIRONMENT=.venvs/py$py uv run --python "$py" pytest -q -m "not integration" {{args}} || failed+=("$py")
    done
    if [ ${#failed[@]} -gt 0 ]; then echo "Failed on: ${failed[*]}"; exit 1; fi

# Run the unit tests on the free-threaded builds
test-free-threaded *args:
    #!/usr/bin/env bash
    set -uo pipefail
    failed=()
    for py in {{free_threaded}}; do
        echo "==> Python $py"
        UV_PROJECT_ENVIRONMENT=.venvs/py$py uv run --python "$py" pytest -q -m "not integration" {{args}} || failed+=("$py")
    done
    if [ ${#failed[@]} -gt 0 ]; then echo "Failed on: ${failed[*]}"; exit 1; fi

# Run the live tests against an Ogmios server (OGMIOS_URL, default ws://localhost:1337)
test-integration *args:
    OGMIOS_URL={{ogmios_url}} uv run pytest -m integration {{args}}

# Run the unit tests with a coverage report
cov:
    uv run pytest -m "not integration" --cov --cov-report=term-missing --cov-report=html

# Check linting and formatting
lint:
    uv run ruff check .
    uv run ruff format --check .

# Fix lint findings and format the code
fmt:
    uv run ruff check --fix .
    uv run ruff format .

# Type-check the package and tests
typecheck:
    uv run ty check

# Lint, type-check and test
check: lint typecheck test

# Build the sdist and wheel into dist/
build:
    rm -rf dist
    uv build

# Update the changelog from commits
changelog:
    uv run cz changelog

# Bump the version and changelog from commits, and tag
bump:
    uv run cz bump --yes </dev/null

# Remove build, test and cache artifacts
clean:
    rm -rf dist .venvs .pytest_cache .ruff_cache .coverage htmlcov
    find . -name __pycache__ -type d -prune -not -path "./.venv/*" -exec rm -rf {} +

# Regenerate src/pyogmios/_generated from the pinned schema (schemas/VERSION)
regen-models:
    uv run python scripts/generate.py

# Check src/pyogmios/_generated matches what the pinned schema generates
check-generated: regen-models
    git diff --exit-code -- src/pyogmios/_generated

# Record fixtures from a live Ogmios server (OGMIOS_URL, default ws://localhost:1337)
record-fixtures:
    OGMIOS_URL={{ogmios_url}} uv run python scripts/record_fixtures.py

# Check blocks from across the chain against the schema and models (add --full for every block)
sweep *args:
    OGMIOS_URL={{ogmios_url}} uv run python scripts/sweep_blocks.py {{args}}
