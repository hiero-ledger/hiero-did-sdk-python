# Hedera AnonCreds Method implementation

## Description

- The document describes selected approach for Hedera Anoncreds Method implementation
- Contains references to recommendations and discussions on this matter in Hedera open-source community

## References

- [AnonCreds Method term reference](https://hyperledger.github.io/anoncreds-spec/#term:anoncreds-method)
- [AnonCreds Methods Registry](https://hyperledger.github.io/anoncreds-methods-registry/)
- [HIP-762: AnonCreds Verifiable Data Registry](https://hips.hedera.com/hip/hip-762)
  - Hedera Improvement Proposal (HIP) which contains initial recommendations and proposals for Hedera Anoncreds implementation
- [GH discussion on HIP-762 PR](https://github.com/hashgraph/hedera-improvement-proposal/pull/762)
- [HCS-1 Standard: File Data Management with Hedera Consensus Service](https://hashgraphonline.com/docs/standards/hcs-1/)
  - Describes unified approach for storing files in HCS
  - Provides good and explicit approach for compressing and chunking data before writing it to Hedera (with hash-based integrity check) + has other existing implementations that can be used for interoperability testing
- [Hedera DID spec](https://github.com/hashgraph/did-method/blob/master/hedera-did-method-specification.md)
- [Indy Credentials Revocation spec](https://github.com/hyperledger/indy-hipe/blob/main/text/0011-cred-revocation/README.md) (more technical)

## General

The goal of Hedera AnonCreds Method is to provide API and capabilities to use Hedera network as AnonCreds Verifiable Data Registry (VDR).

Core design points:

- AnonCreds objects identifiers format
- Storage approach for AnonCreds objects/entities
- Revocation support
  - VDR part is not so complex by nature, but still introduces a number of technical questions (storage approach for revocation list/deltas API, accumulator values persistence, etc.)

## Hedera storage for AnonCreds entities

### Schema and Cred Def

- Unlike DID documents, schema and Cred Def entities are immutable → there is no need to implement complex state management similar to what we have in [Hedera DID spec](https://github.com/hashgraph/did-method/blob/master/hedera-did-method-specification.md)
- JSON data for Schema and Cred Def could be stored as immutable file, there are two general options:
  - Hedera File Service - the idea was discarded due to non-free read operations
  - HCS storage implemented according to HCS-1 standard - optimal approach
- The chosen approach assumes that Schema and Cred Def data is stored and managed as immutable HCS-1 files
  - Each Schema and Cred Def instance has a unique topic ID, in fact it's the only thing that needed to read the data from HCS

### Revocation Registry Definition and Entry

- The optimal approach for Reg Entries will be to manage them in a single HCS topic - this will allow reading messages stream using from/to timestamps, calculating deltas and etc.
- Reg Def is managed independently under separate HCS topic, it results in cleaner solution - we're going to avoid additional filtering logic and related potential inconveniences (there will not be multiple reasons to read messages from particular topic)

## Anoncreds identifiers

### Contradictions with HIP-762

- Initial proposal for HIP-762 references [Cardano Anoncreds Method](https://github.com/roots-id/cardano-anoncreds/blob/main/cardano-anoncred-methods.md) as base/example approach
- This includes implementation of [DID-Linked resources](https://wiki.trustoverip.org/display/HOME/DID-Linked+Resources+Specification) approach for identifiers and entities metadata
- In further discussion of HIP proposal, it was suggested to exclude DID-Linked resources usage from Hedera Anoncreds Method
  - There is a good amount of conceptual reasoning for such decision, but it can be summarized as redundancy comparing to more straightforward use of HCS
- Indy-like identifiers format was proposed as alternative: "did/object-family/object-family-version/object-type/object-type-identifier"

### Current approach

- Indy-inspired format + HCS topic ID as object ID: `{publisherDid}/anoncreds/{anoncredsVersion}/{entityType}/{hcsTopicId}`
- Works well for HCS-1 files and basically for any Hedera SSI entity managed using HCS

## Revocation support

### General

- Most technically complex part of Anoncreds implementation, but our focus here is to provide Hedera VDR API and functionality
- [ACA-Py revocation documentation](https://github.com/openwallet-foundation/acapy/blob/main/docs/gettingStarted/CredentialRevocation.md) was used as a reference for required API and functionality
- General approach is to implement revocation support in Indy-like way while leveraging Hedera HCS

### Technical questions and chosen solutions

#### Tails file storage

- Tails files are immutable, but potentially large - should not be stored in a ledger
- The optimal approach is to delegate tails files management to end-application, taking into the account that SSI agents like [ACA-Py](https://github.com/openwallet-foundation/acapy) usually do this part well

#### Read operations approach for entities

- Revocation Registry Definition
  - Stored as HCS-1 file → file reading according to HCS-1 standard
- Revocation Registry Entry
  - Reading of HCS topic messages stream with support for from/to timestamps (essential for revocation list API)

#### Accumulator values persistence

- For instance, in ACA-Py Indy implementation, current and previous accumulator values are included in each Rev Reg Entry (except for initial one, it doesn't have any previous value)
- The size of accumulator value depends on max amount of credentials in Rev Reg and can be large enough to not fit in HCS message max size
- Persisting these values is not absolutely necessary - can be potentially calculated on SDK side, but the process is complex and heavy
  - Calculated accumulator values could potentially be cached in SDK, but it also can be a bit tricky as requested revocation state timestamp is arbitrary
- Summary
  - If accumulator values are persisted, we can avoid heavy work on SDK side + direct interactions with tails files - more valuable for reducing complexity
  - The optimal solution is to store accumulator values in entries and deal with HCS messages compression
    - HCS-1 compression + chunking cannot be used directly as we want to read Rev Reg Entries as a message stream from a single topic
    - Message compression alone works well producing <500 bytes messages for accumulator values in revocation registries that support 100K credentials
    - Message chunking on a single HCS topic looks to be redundant for accumulator messages case, but, if implemented, will look similar to approach implemented in Hedera Java SDK (and potentially can be reused from there)

#### Delta resolution and API on SDK side and storage approach for Rev Reg Entries

Delta can be resolved using HCS timestamps and Rev Reg Entries message stream (taking into the account that we persist accumulator values in entries)

#### Indy-like issuance type support for revocation registries

- `ISSUANCE_BY_DEFAULT` is expected behavior by [ACA-Py](https://github.com/openwallet-foundation/acapy) and [Anoncreds RS](https://github.com/hyperledger/anoncreds-rs), so it makes sense to stick to it in our implementation as well.
- Assumes "issued" state for all credentials managed by revocation registry - there is no need to update registry and accumulator value when credential is issued
