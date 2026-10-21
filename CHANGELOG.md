## v1.0.0 (2026-10-21)

A rewrite for **Ogmios v7**, which replaced the protocol 0.7 used (Ogmios v5). Breaking: the import is
`pyogmios` (was `pyogmios_client`), Python 3.11+ is required, and the API is new. See
[Migrating from 0.7](https://kingpin-apps.github.io/pyogmios/migration/).

### Feat

- per-call timeout on every typed query
- add the pyogmios command line
- add chain sync, ledger state and mempool protocols
- generate typed query methods and per-code transaction errors
- add async and sync clients over WebSocket and HTTP
- generate v7 models and method table from the schema

### Fix

- expose the intersection and tip on the sync chain sync
- resume chain sync with the client's reconnect policy
- retrieve errors of chain sync requests lost to a dropped connection

### Refactor

- remove the v5 client
- rename package to pyogmios under src/

## 0.7.4 (2023-11-22)

### Refactor

- update and migrate to Pydantic V2

## 0.7.3 (2023-07-12)

### Fix

- remove extra on_message
- add missing forward refs

## 0.7.2 (2023-06-26)

### Fix

- handle MissingRequiredDatumsError

## 0.7.1 (2023-06-19)

### Fix

- use threading events in websocket on open
- use era mismatch result

## 0.7.0 (2023-06-18)

### Feat

- add tx submission code
- add tx monitor code
- add state query code
- add chain sync client code

### Fix

- use new models and enums
- add necessary utils
- sort out all models
- complete chain sync client code and add tests

### Refactor

- add enums
