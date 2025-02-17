# Hiero DID SDK Python

[![Release](https://img.shields.io/github/v/release/hiero-ledger/hiero-did-sdk-python)](https://img.shields.io/github/v/release/hiero-ledger/hiero-did-sdk-python)
[![Build status](https://img.shields.io/github/actions/workflow/status/hiero-ledger/hiero-did-sdk-python/main.yml?branch=main)](https://github.com/hiero-ledger/hiero-did-sdk-python/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/hiero-ledger/hiero-did-sdk-python/branch/main/graph/badge.svg)](https://codecov.io/gh/hiero-ledger/hiero-did-sdk-python)
[![Commit activity](https://img.shields.io/github/commit-activity/m/hiero-ledger/hiero-did-sdk-python)](https://img.shields.io/github/commit-activity/m/hiero-ledger/hiero-did-sdk-python)
[![License](https://img.shields.io/github/license/hiero-ledger/hiero-did-sdk-python)](https://img.shields.io/github/license/hiero-ledger/hiero-did-sdk-python)

This repository contains the Python SDK that enables developers to manage Decentralized Identifiers (DIDs) and AnonCreds Verifiable Credentials on the Hedera network using the Hedera Consensus Service.

This library is using [Hiero Python SDK](https://github.com/hiero-ledger/hiero-sdk-python).

# Table of contents

1. [Documentation](#documentation)
2. [Getting started](#getting-started)
3. [Configuration](#configuration)
4. [Contributing](CONTRIBUTING.md)
   
## Overview

Identity networks are set of artifacts on Hedera Consensus Service that allow applications to share common channels to publish and resolve DID documents, issue verifiable credentials and control their validity status. These artifacts include:
* address book - a file on Hedera File Service that provides information about HCS topics and appnet servers,
* DID topic - an HCS topic intended for publishing DID documents,
* and VC topic - an HCS topic playing a role of verifiable credentials registry.
   
This SDK is designed to simplify :
* creation of identity networks within appnets, that is: creation and initialization of the artifacts mentioned above,
* generation of decentralized identifiers for Hedera DID Method and creation of their basic DID documents,
* creation (publishing), update, deletion and resolution of DID documents in appnet identity networks,
* issuance, revocation and status verification of Verifiable Credentials.
   
The SDK does not impose any particular way of how the DID or verifiable credential documents are constructed.

## Documentation

### Dev and API

We're planning to publish dev guides along with [mkdocs](https://www.mkdocs.org/)-generated API documentation to GH pages in near future.
You can find [documentation sources in repo](docs/dev).

Meanwhile, dev guides have been added to this README for convenience.

If you're planning to contribute to the project, please also check [contribution guidelines](CONTRIBUTING.md).

### Design

SDK design documentation can be found in corresponding [repo folder](docs/design).

## Dev environment

The project uses Makefile for dev scripts. You can view available commands by running:

```bash
make help
```

Core commands are listed below:

#### Install dependencies and tools

```bash
make install
```

#### Run code quality checks

```bash
make check
```

#### Run tests

```bash
make test
```

#### Build artifacts

```bash
make build
```

## Getting started

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/) (at least 1.8.4)
- NodeJS and npm (used by pre-commit hooks)
- Tools for Makefile support (Windows only)
  - Can be installed with [chocolatey](https://chocolatey.org/): `choco install make`

### Install package (from Git source)

```bash
pip install git+https://github.com/hiero-ledger/hiero-did-sdk-python@main
```

Please note that PyPi package will soon be published and replace Git source dependency as recommended installation method.

### Example usage

Here you can find basic SDK usage examples.

For more complex examples, please refer to SDK integration tests:

- [Hedera DID](https://github.com/hiero-ledger/hiero-did-sdk-python/blob/main/tests/integration/test_hedera_did.py)
- [AnonCreds registry](https://github.com/hiero-ledger/hiero-did-sdk-python/blob/main/tests/integration/test_hedera_anoncreds_registry.py)

#### Create Hedera Client (for testnet)

```python
from hiero_sdk_python import Client, Network, AccountId, PrivateKey

client = Client(
    network=Network("testnet")
)

client.set_operator(AccountId.from_string("OPERATOR_ID"), private_key=PrivateKey.from_string("OPERATOR_KEY"))
```

#### Register new Hedera DID on testnet network and add DID service

```python
from hiero_did_sdk_python import HederaDid

did = HederaDid(client=client, private_key_der="private_key_der")

await did.register()

await did.add_service(
    id_=f"{did.identifier}#service-1", service_type="LinkedDomains", service_endpoint="https://example.com/vcs"
)
```

#### Resolve existing Hedera DID

```python
from hiero_did_sdk_python import HederaDidResolver

resolver = HederaDidResolver(client)

resolution_result = await resolver.resolve(
    "did:hedera:testnet:zvAQyPeUecGck2EsxcsihxhAB6jZurFrBbj2gC7CNkS5o_0.0.5063027")
```

#### Create AnonCreds credential schema and credential definition

```python
from hiero_did_sdk_python import HederaAnonCredsRegistry, AnonCredsSchema, AnonCredsCredDef, CredDefValue, CredDefValuePrimary

issuer_did = "did:hedera:testnet:zvAQyPeUecGck2EsxcsihxhAB6jZurFrBbj2gC7CNkS5o_0.0.5063027"
registry = HederaAnonCredsRegistry(client)

schema = AnonCredsSchema(
    name="schema-name",
    issuer_id=issuer_did,
    attr_names=["name", "age"],
    version="1"
)

schema_registration_result = await registry.register_schema(schema, issuer_did, "OPERATOR_KEY_DER")

cred_def = AnonCredsCredDef(
    schema_id=schema_registration_result.schema_state.schema_id,
    issuer_id=issuer_did,
    value=CredDefValue(primary=CredDefValuePrimary(...)),
    tag="cred-def-tag"
)

cred_def_registration_result = await registry.register_cred_def(cred_def, issuer_did, "OPERATOR_KEY_DER")
```

## Configuration

At the moment, SDK comes with following configuration capabilities:

- Hedera Client configuration
- Cache implementation (optional)
- Logger configuration (optional)

### Hedera Client configuration

Configuration consists from two parts:

- Network configuration
  - Basic configuration is lightweight and consists from selection of specific network ("mainnet", "testnet", "
    previewnet"), complex parts are handled by Hedera Python SDK
  - Custom configuration can be provided, if necessary
- Hedera operator (account) configuration
  - Essentially, account "credentials" that will be used for Hedera network integration and paying fees
  - Needs to be provided explicitly and can be changed for specific Hedera Client instance via provider class

#### Examples

Create client for Testnet and set operator config:

```python
from hiero_sdk_python import Client, Network, AccountId, PrivateKey

client = Client(
    network=Network("testnet")
)

client.set_operator(AccountId.from_string("OPERATOR_ID"), private_key=PrivateKey.from_string("OPERATOR_KEY"))
```

Create client provider with custom network config:

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

### Cache implementation

SDK utilizes cache to optimize read operations and provides an option to customize cache implementation (individually
for each resolver instance).

By default, [in-memory cache implementation](https://github.com/hiero-ledger/hiero-did-sdk-python/blob/main/hiero_did_sdk_python/utils/cache.py#L112) is used.

You can create custom cache implementation by inheriting [Cache base class](https://github.com/hiero-ledger/hiero-did-sdk-python/blob/main/hiero_did_sdk_python/utils/cache.py#L25).
Custom cache instance needs to be provided in resolver constructor arguments.

Classes that accept custom cache implementation:

- [HederaDidResolver](https://github.com/hiero-ledger/hiero-did-sdk-python/blob/main/hiero_did_sdk_python/did/hedera_did_resolver.py)
- [HederaAnonCredsRegistry](https://github.com/hiero-ledger/hiero-did-sdk-python/blob/main/hiero_did_sdk_python/anoncreds/hedera_anoncreds_registry.py)

#### Example

```python
from hiero_did_sdk_python import Cache, HederaDidResolver

class CustomCache(Cache):
  ...

custom_cache_instance = CustomCache[str, object]()

resolver = HederaDidResolver(client, custom_cache_instance)
```

### Logger configuration

Logger configuration supports following properties that can be set with environment variables:

- Log level
  - Env variable name: `HEDERA_DID_SDK_LOG_LEVEL`
  - Currently supported values: "DEBUG", "INFO", "WARN", "ERROR"
- Log format (in string representation)
  - Env variable name: `HEDERA_DID_SDK_LOG_FORMAT`
  - For log format pattern reference, please see Python docs:
    - [Formatter objects](https://docs.python.org/3/library/logging.html#formatter-objects)
    - [Log record attributes](https://docs.python.org/3/library/logging.html#logrecord-attributes)
