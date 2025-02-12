# Adoption of specifications changes

SSI specifications are known to be in active development process and sometimes introducing breaking changes.

Good example is the current state of [OID4VC protocols](https://openid.net/sg/openid4vc/specifications/) where new drafts are actively releasing, and it's not uncommon to find implementations that use incompatible protocols versions (as well as projects that try and support multiple versions at the same time).

Specifically, this SDK contains implementations of [Hedera DID spec](https://github.com/hashgraph/did-method/blob/master/hedera-did-method-specification.md) and part of [AnonCreds spec](https://hyperledger.github.io/anoncreds-spec/). Both can and will change in the future, so we want to outline key parts of changes adoption process from SDK perspective.
Note that [AnonCreds v2 spec](https://github.com/hyperledger/anoncreds-spec-v2) is being actively developed

### AnonCreds spec

As we're including AnonCreds version in object identifiers (see [Hedera AnonCreds Method implementation page](./hedera-anoncreds-method.md#anoncreds-identifiers)), versioning will be quite simple.

Moreover, all core AnonCreds objects are immutable (Schema, Cred Def, Revocation Registry Definition), so the approach for migration to a new spec should not include any operations on existing data - it's natural that new objects must be created for a new version.
Backwards compatibility will also be trivial due to explicit versioning provided by object identifiers formats.

General approach for adopting new spec version can be described as following:

- Create `v1` and `v2` folders in [AnonCreds module](../../hiero_did_sdk_python/anoncreds)
- Move existing implementation to `v1`
- Implement [models](../../hiero_did_sdk_python/anoncreds/models), [AnonCreds registry](../../hiero_did_sdk_python/anoncreds/hedera_anoncreds_registry.py) and any required utils for new version in `v2` folder
- (Optional) Add root AnonCreds registry that will abstract out `v1` and `v2` specific implementations by using object identifiers for determining required version
  - For example, if we want to resolve arbitrary Schema by ID we can lookup AnonCreds version in identifier and use corresponding version-specific registry implementation

### DID spec

Changes to DID spec would be more complex to handle, mainly due to mutable nature of DID document.

Most problematic part here is backwards compatibility. For instance, if some field of HCS DID event will be renamed, we will end up with a number of outdated and immutable HCS messages for previously created DID.
To mitigate that, backwards compatibility logic needs to be added for HCS DID events (messages) processing.

Potential versioning is less trivial, but not really required. Actual approach here is responsibility of DID spec.

General approach for adopting DID spec changes:

- Update [HCS DID events](../../hiero_did_sdk_python/did/hcs/events) and/or [Hedera DID class](../../hiero_did_sdk_python/did/hedera_did.py) as necessary
- Analyze backwards compatibility issues caused by data in previously created HCD messages
- Add backwards compatibility logic in [DID Document messages processing methods](../../hiero_did_sdk_python/did/did_document.py)
