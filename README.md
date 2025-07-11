# Hiero DID SDK Python

[![Release](https://img.shields.io/github/v/release/hiero-ledger/hiero-did-sdk-python)](https://github.com/hiero-ledger/hiero-did-sdk-python/releases)
[![Build status](https://img.shields.io/github/actions/workflow/status/hiero-ledger/hiero-did-sdk-python/main.yml?branch=main)](https://github.com/hiero-ledger/hiero-did-sdk-python/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/hiero-ledger/hiero-did-sdk-python/branch/main/graph/badge.svg)](https://codecov.io/gh/hiero-ledger/hiero-did-sdk-python)
[![Commit activity](https://img.shields.io/github/commit-activity/m/hiero-ledger/hiero-did-sdk-python)](https://github.com/hiero-ledger/hiero-did-sdk-python/commits/main)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/hiero-ledger/hiero-did-sdk-python/badge)](https://scorecard.dev/viewer/?uri=github.com/hiero-ledger/hiero-did-sdk-python)
[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/10697/badge)](https://bestpractices.coreinfrastructure.org/projects/10697)
[![License](https://img.shields.io/github/license/hiero-ledger/hiero-did-sdk-python)](https://github.com/hiero-ledger/hiero-did-sdk-python/blob/main/LICENSE)

This repository contains the Python SDK that enables developers to manage Decentralized Identifiers (DIDs) and AnonCreds Verifiable Credentials on the Hedera network using the Hedera Consensus Service.

This library is using [Hiero Python SDK](https://github.com/hiero-ledger/hiero-sdk-python).

# Table of contents

1. [Overview](#overview)
2. [Documentation](#documentation)
3. [Getting started](#getting-started)
4. [Configuration](#configuration)
5. [Contributing](CONTRIBUTING.md)

## Overview

Decentralized identity ecosystems are built upon decentralized identifiers (DIDs) and verifiable credentials (VCs) standards, providing necessary functionality to publish and resolve DID documents and issue/verify credentials (claims).

Data model of such ecosystems rely on [Verifiable Data Registries (VDRs)](https://w3c.github.io/vc-data-model/#dfn-verifiable-data-registries), commonly represented by decentralized ledgers.

[Hiero](https://hiero.org/), as an open-source Decentralized Ledger Technology (DLT), is a great VDR option providing high-performance and low costs of operations.
Hedera, while being built on Hiero, is a large and trusted network that will be a great choice for solutions searching for high-reliability.

In particular, Hedera and other Hiero-based networks can be used as VDR for [Hedera DID Method](https://github.com/hashgraph/did-method/blob/master/hedera-did-method-specification.md) and [AnonCreds Verifiable Credentials](https://github.com/hyperledger/anoncreds-spec) by leveraging Hedera Consensus Service (HCS).

This SDK is designed to simplify:

- Creation and management of Hedera DID documents
- Creation and management of AnonCreds resources
- Adoption of Hiero-based VDRs for AnonCreds use cases
- Empowering new and existing Python-based agent implementations with high-performance and low operational costs provided by Hiero

## Documentation

### Dev and API

You can find dev documentation on [GH pages](https://hiero-ledger.github.io/hiero-did-sdk-python/).

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

### Install package

```bash
pip install hiero-did-sdk-python
```

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

## Contributing to this Project

Whether you’re fixing bugs, enhancing features, or improving documentation, your contributions are important — let’s build something great together!

For instructions on how to contribute to this repo, please
review the [Contributing Guide for the Hiero DID SDK](CONTRIBUTING.md).

More instructions for contribution can be found in the
[Global Contributing Guide](https://github.com/hiero-ledger/.github/blob/main/CONTRIBUTING.md).

## Code of Conduct

Hiero uses the Linux Foundation Decentralised Trust [Code of Conduct](https://www.lfdecentralizedtrust.org/code-of-conduct).

## License

[Apache License 2.0](LICENSE)
