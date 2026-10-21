# Contributing

## Set up

pyogmios uses [uv](https://docs.astral.sh/uv/) and [just](https://just.systems/).

```shell
git clone https://github.com/Kingpin-Apps/pyogmios
cd pyogmios
just sync                 # install the project and every dependency group
uv run pre-commit install # lint and format on commit, check commit messages
```

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`,
`docs:`, `test:`...): the changelog and version numbers are made from them.

## Checks

```shell
just check               # lint, type-check (ty) and the unit tests
just test-all            # unit tests on Python 3.11, 3.12, 3.13, 3.14 and 3.15
just test-free-threaded  # unit tests on 3.14t and 3.15t
just test-properties     # property-based tests over every type (about a minute)
just cov                 # coverage report (CI requires 95%)
```

The unit tests need no server: they run against a fake Ogmios that replays recorded responses. Every
warning fails a test.

## The devnet

`devnet/` runs a private Cardano network with Ogmios 7, in Docker:

```shell
just devnet-up      # a fresh devnet, Ogmios on ws://localhost:1338 (about 10 seconds)
just test-devnet    # the live tests, and tests that sign and submit real transactions
just devnet-down
```

Each start generates a new genesis, stake pool, DRep, committee member and funded keys with
`cardano-cli`, written to `devnet/.state` (ignored by git), so no keys are committed and every run
starts clean. The chain starts in Conway, with 0.1-second slots.

To test against another server, such as a synced preview node: `OGMIOS_URL=ws://... just test-integration`.

## Generated code

`src/pyogmios/_generated` is generated from the Ogmios schema pinned in `schemas/`:

```shell
just regen-models    # after changing scripts/build_schema.py or the pinned schema
```

Never edit it by hand; CI fails if it differs from what the schema generates. Where the schema and the
server disagree, add a documented correction to `CORRECTIONS` in `scripts/build_schema.py`, with the
evidence, and a fixture that proves it.

## Fixtures

`tests/fixtures` holds real responses recorded from a preview node:

```shell
just record-fixtures   # OGMIOS_URL, default ws://localhost:1337
```

`just sweep` checks blocks from across a whole chain against the schema and the models
(`just sweep --full` checks every block).

## Docs

```shell
uv run mkdocs serve    # http://127.0.0.1:8000
```

Every Python example in the docs is compiled by the unit tests; examples marked `<!-- test: run -->`
run against the devnet in CI.

## Releasing

`just bump` makes the version and changelog from the commits and tags the release; pushing the `v*`
tag publishes to PyPI and the docs to GitHub Pages.
