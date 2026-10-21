# Command line

Installing pyogmios adds a `pyogmios` command (also `python -m pyogmios`), for quick checks and scripts.

```shell
pyogmios health                          # version, network, sync progress and tip
pyogmios tip                             # the tip and block height
pyogmios query epoch                     # any query, by its short or full name
pyogmios query ledger-state/tip
pyogmios query utxo '{"addresses": ["addr_test1..."]}'
pyogmios follow --from origin --headers  # chain events, one JSON document per line
pyogmios follow --from 1234.abcd... --count 100
pyogmios mempool --full                  # transactions as they enter the mempool
pyogmios submit tx.signed                # hex, CBOR bytes, or a cardano-cli text envelope
pyogmios evaluate tx.raw
```

- **Server:** `--url`, else `$OGMIOS_URL`, else `ws://localhost:1337`. Options work before or after the
  command.
- **Output:** JSON with Ogmios's own field names, indented in a terminal and compact when piped
  (`--pretty` and `--compact` choose). Streams print one document per line, ready for `jq`.
- **Exit codes:** 0 on success, 1 for an error from the server (its data goes to standard error), 2 for
  a usage error, 3 when the server cannot be reached.

```shell
pyogmios follow --headers | jq -c 'select(.direction == "forward") | .block | {height, id}'
```

## Help

<!-- cli:help -->
