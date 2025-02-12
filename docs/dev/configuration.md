# Configuration

At the moment, SDK comes with following configuration capabilities:

- Hedera Client configuration
- Cache implementation (optional)
- Logger configuration (optional)

## Hedera Client configuration

Configuration consists from two parts:

- Network configuration
  - Basic configuration is lightweight and consists from selection of specific network ("mainnet", "testnet", "
    previewnet"), complex parts are handled by Hedera Python SDK
  - Custom configuration can be provided, if necessary
- Hedera operator (account) configuration
  - Essentially, account "credentials" that will be used for Hedera network integration and paying fees
  - Needs to be provided explicitly and can be changed for specific Hedera Client instance via provider class

### Examples

#### Create client for Testnet and set operator config

```python
from hiero_sdk_python import Client, Network, AccountId, PrivateKey

client = Client(
    network=Network("testnet")
)

client.set_operator(AccountId.from_string("OPERATOR_ID"), private_key=PrivateKey.from_string("OPERATOR_KEY"))
```

#### Create client provider with custom network config

```python
from hiero_sdk_python import Client, Network, AccountId, PrivateKey

TESTNET_NODES = [
    ("0.testnet.hedera.com:50211", AccountId(0, 0, 3)),
    ("1.testnet.hedera.com:50211", AccountId(0, 0, 4))
]

client = Client(
    network=Network(network="testnet", nodes=TESTNET_NODES, mirror_address="hcs.testnet.mirrornode.hedera.com:5600"),
)
client.set_operator(AccountId.from_string("OPERATOR_ID"), private_key=PrivateKey.from_string("OPERATOR_KEY"))
```

## Cache implementation

SDK utilizes cache to optimize read operations and provides an option to customize cache implementation (individually
for each resolver instance).

By default, [in-memory cache implementation](modules/common.md#hiero_did_sdk_python.utils.cache.MemoryCache) is used.

You can create custom cache implementation by inheriting [Cache base class](modules/common.md#hiero_did_sdk_python.utils.cache.Cache).
Custom cache instance needs to be provided in resolver constructor arguments.

Resolver classes that accept custom cache implementation:

- [HederaDidResolver](modules/did.md#hiero_did_sdk_python.did.hedera_did_resolver.HederaDidResolver)
- [HederaAnonCredsRegistry](modules/anoncreds.md#hiero_did_sdk_python.anoncreds.hedera_anoncreds_registry.HederaAnonCredsRegistry)

### Example

```python
from hiero_did_sdk_python import Cache, HederaDidResolver

class CustomCache(Cache):
  ...

custom_cache_instance = CustomCache[str, object]()

resolver = HederaDidResolver(client, custom_cache_instance)
```

## Logger configuration

Logger configuration supports following properties that can be set with environment variables:

- Log level
  - Env variable name: `HEDERA_DID_SDK_LOG_LEVEL`
  - Currently supported values: "DEBUG", "INFO", "WARN", "ERROR"
- Log format (in string representation)
  - Env variable name: `HEDERA_DID_SDK_LOG_FORMAT`
  - For uniformity purposes, the SDK expects format string to correspond with Java (
    `ch.qos.logback:logback-classic`) [pattern](https://logback.qos.ch/manual/layouts.html#ClassicPatternLayout)
