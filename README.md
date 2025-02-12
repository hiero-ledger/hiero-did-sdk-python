# Hiero DID SDK Python

[![Release](https://img.shields.io/github/v/release/hiero-ledger/hiero-did-sdk-python)](https://img.shields.io/github/v/release/hiero-ledger/hiero-did-sdk-python)
[![Build status](https://img.shields.io/github/actions/workflow/status/hiero-ledger/hiero-did-sdk-python/main.yml?branch=main)](https://github.com/hiero-ledger/hiero-did-sdk-python/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/hiero-ledger/hiero-did-sdk-python/branch/main/graph/badge.svg)](https://codecov.io/gh/hiero-ledger/hiero-did-sdk-python)
[![Commit activity](https://img.shields.io/github/commit-activity/m/hiero-ledger/hiero-did-sdk-python)](https://img.shields.io/github/commit-activity/m/hiero-ledger/hiero-did-sdk-python)
[![License](https://img.shields.io/github/license/hiero-ledger/hiero-did-sdk-python)](https://img.shields.io/github/license/hiero-ledger/hiero-did-sdk-python)

The repository contains the Python SDK for managing DID Documents and AnonCreds Verifiable Credentials registry using
Hedera Consensus Service.

Documentation:

- ~~See [SDK docs](https://hiero-ledger.github.io/hiero-did-sdk-python/)~~
  - Not published yet, see [src in repo](docs/dev)
- Design documentation can be found in [repo folder](docs/design)

## Getting started

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/) (at least 1.8.4)
- NodeJS and npm (used by pre-commit hooks)
- Tools for Makefile support (Windows only)
  - Can be installed with [chocolatey](https://chocolatey.org/): `choco install make`

### Environment

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

## Releasing a new version

- Create a [new release](https://github.com/hiero-ledger/hiero-did-sdk-python/releases/new) on GitHub
- Create a new tag in the form `*.*.*`
