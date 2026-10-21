# Clients and connections

pyogmios has two clients with the same methods:

- **`pyogmios.AsyncClient`** for asyncio code: every method is a coroutine.
- **`pyogmios.Client`** for everything else. It runs an `AsyncClient` on a private event loop in a
  background thread, so the two behave the same. It is safe to share between threads.

Open them with `with` / `async with`, which connects and closes for you. Without it, a client connects
on its first request; call `close()` when you are done.

```python
import pyogmios

with pyogmios.Client("ws://localhost:1337") as client:
    print(client.ledger_state.epoch())

client = pyogmios.Client("ws://localhost:1337")
print(client.ledger_state.epoch())  # connects here
client.close()
```

## URLs and transports

The URL's scheme picks the transport:

| URL | Transport | What works |
|---|---|---|
| `ws://`, `wss://` | WebSocket | Everything. Many requests can be in flight on one connection. |
| `http://`, `https://` | HTTP POST, one request per call | Queries, `submit_transaction`, `evaluate_transaction`. |

Chain sync, the mempool and acquiring a ledger state keep state on the connection, so over HTTP they
raise `StatefulOverHttpError`. (Ogmios answers them over HTTP, but every HTTP request is a new session,
so the answers would be meaningless.)

For a hosted Ogmios, include the path the provider gives you and any API key header:

```python
client = pyogmios.Client(
    "wss://ogmios.example.com/v7/",
    headers={"api-key": "..."},
)
```

## Concurrency

On WebSocket, requests from many tasks share one connection: each answer is matched to its request
by id, so nothing waits for anything else.

```python
import asyncio

async with pyogmios.AsyncClient() as client:
    pools, parameters, tip = await asyncio.gather(
        client.ledger_state.stake_pools(),
        client.ledger_state.protocol_parameters(),
        client.network.tip(),
    )
```

## Timeouts

Every request waits up to `timeout` seconds (60 by default) and then raises `OgmiosTimeoutError`, which
is also a builtin `TimeoutError`. Override it per call, or pass `None` to wait forever:

```python
client = pyogmios.Client(timeout=10)
provenance = client.ledger_state.rewards_provenance(timeout=120)  # a slow query
proposals = client.call("queryLedgerState/governanceProposals", timeout=None)  # no limit
```

`open_timeout` (10 seconds) limits opening the connection. Some mainnet queries, such as
`delegate_representatives()` and `rewards_provenance()`, return tens of megabytes and can take a few
seconds; message size is not limited.

## Reconnecting

When the WebSocket connection drops, every request in flight fails at once with
`OgmiosConnectionError` (also a builtin `ConnectionError`), and the next request reconnects. Connecting,
the first time or again, retries as the `reconnect` policy says:

```python
from pyogmios import Reconnect

client = pyogmios.Client(reconnect=Reconnect(attempts=10, initial_delay=1, max_delay=30))
client = pyogmios.Client(reconnect=None)  # never retry
```

The delay before retry *n* is `initial_delay * factor ** n`, capped at `max_delay`, with up to `jitter`
of it added or removed at random. The defaults are 5 attempts, from 0.5 to 10 seconds.

`client.generation` counts the connections opened. Chain sync, an acquired ledger state and the mempool
use their own connections and handle a drop themselves: see
[Following the chain](chain-sync.md#when-the-connection-drops).

## The version check

On connect, the client reads the server's `/health` to check it runs Ogmios 7:

| `check_version=` | Older than 7 | Newer than 7, or unknown |
|---|---|---|
| `"warn"` (default) | raises `ServerVersionError` | warns |
| `"strict"` | raises `ServerVersionError` | raises `ServerVersionError` |
| `"off"` | not checked | not checked |

The health read on connect is kept in `client.server_health`.

## Health

`client.health()` reads `/health` at any time:

<!-- test: run -->
```python
import pyogmios

with pyogmios.Client("ws://localhost:1337") as client:
    health = client.health()
    print(health.version, health.network, health.current_era)
    print(
        f"synced: {health.network_synchronization:.2%}",
        "ready" if health.is_synced else "catching up",
    )
    print("tip:", health.last_known_tip)
```

## TLS

`wss://` and `https://` verify certificates with the system's trust store. Pass `ssl_context=` for a
private CA or client certificates.

## Logging

pyogmios logs to the `pyogmios` logger, and never configures logging itself. Connection problems are
warnings; every request and response is at debug level:

```python
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("pyogmios").setLevel(logging.DEBUG)
```

## Calling any method by name

The typed methods cover every Ogmios method, but you can also call one by its Ogmios name:

- `client.call(method, params)` validates `params` and returns the parsed result.
- `client.request(method, params)` sends `params` as given and returns plain JSON.

```python
epoch = client.call("queryLedgerState/epoch")
raw_tip = client.request("queryNetwork/tip")  # {"slot": ..., "id": "..."}
```
