import asyncio
import json
import time

import pytest
from hiero_sdk_python import Client, PrivateKey

from hiero_did_sdk_python import (
    AnonCredsCredDef,
    AnonCredsRevList,
    AnonCredsRevRegDef,
    AnonCredsSchema,
    CredDefValue,
    CredDefValuePrimary,
    CredDefValueRevocation,
    HederaAnonCredsRegistry,
    HederaDid,
    HederaDidResolver,
    RevRegDefValue,
)
from hiero_did_sdk_python.anoncreds.utils import parse_anoncreds_identifier
from hiero_did_sdk_python.utils.keys import get_key_type

# In real scenario, these credential definition values are provided by AnonCreds implementation

DEMO_CRED_DEF_VALUE_PRIMARY = CredDefValuePrimary(
    n="0954456694171", s="0954456694171", r={"key": "value"}, rctxt="0954456694171", z="0954456694171"
)

DEMO_CRED_DEF_VALUE_REVOCATION = CredDefValueRevocation(
    g="1 1F14F&ECB578F 2 095E45DDF417D",
    g_dash="1 1D64716fCDC00C 1 0C781960FA66E3D3 2 095E45DDF417D",
    h="1 16675DAE54BFAE8 2 095E45DD417D",
    h0="1 21E5EF9476EAF18 2 095E45DDF417D",
    h1="1 236D1D99236090 2 095E45DDF417D",
    h2="1 1C3AE8D1F1E277 2 095E45DDF417D",
    htilde="1 1D8549E8C0F8 2 095E45DDF417D",
    h_cap="1 1B2A32CF3167 1 2490FEBF6EE55 1 0000000000000000",
    u="1 0C430AAB2B4710 1 1CB3A0932EE7E 1 0000000000000000",
    pk="1 142CD5E5A7DC 1 153885BD903312 2 095E45DDF417D",
    y="1 153558BD903312 2 095E45DDF417D 1 0000000000000000",
)

DEMO_REV_REG_DEF_VALUE = RevRegDefValue(
    public_keys={
        "accumKey": {
            "z": "1 0CBE9CCA7C9C3C89D8BB8CC16E3E6ACC2887474B5469669ED5DE842D0D425113 1 15DE8164A6C9667EAB9D59F9E73BE644E8671C1DC896B0FA90A640D11D999C3A 1 2517D5E5BCBC6D7079EB81BBE3DE09A2E855B12341AEE16F840CF9B2701FA96D 1 1520D4C0D90FFD3565980D0F71879D7041706519E9ED29AA3FD5AAD3DDC438CC 1 0671A9C0335F6CDB354D58EA63A52A277A8FEC84E876F385AEB374183BF4A24A 1 05C61C557C8B235C831B2F74394610F12AFDDCD6EE29664162DB4D5774E7627D 1 0273D4E4080D96DA8B769D174CD7362DB53E9CD6BD9914A9FF6C2FAB76B3F028 1 00C481F3ED437AB26139D1EBDDB174B6653C6D1E34C288B169A11A05BD7A3174 1 1996E05B68E6D9E7604BA4EC8C4DC18B46A35C38BFFE3CE5E728E77B42462DED 1 1A5C682727AEA9B0C09A83306947B879EC641682DE4BEF40D9150E0E8CF66013 1 12393982C425D6B7683D0ADCB035D1E6A9CE26F14295168CFA8062CB5E28874C 1 1FE691B3523A4C8BAB667AE3C5CAD4D88124A320FBF1A0412FE64281868199FE"
        }
    },
    max_cred_num=10,
    tails_location="demo-tails-location",
    tails_hash="demo_tails_hash",
)

DEMO_REV_LIST_ACCUM = "21 1200126E528235C2C22071C3F573985E6E07F49217414A0490482BE8E14529582 21 14740BF808146F9CF497ED63D988AAB96D01F1F5444A7C13CEAB695C0775E751A 6 80DEDD4B010823E0D1E0D5B2DBF3730DD71C783886D090C5EE9C31F308A90433 4 1EC552DFED96251A8921E36F609F067008F3F71299F3102F8C79BB2724D741CF 6 846CEEF4639A624AFD77B25EE8E9B65526ACBD4D2947E9317A9C0F7F508B718C 4 2ECC4BF26E413FF2C6D73DBE32023D9208FCE0D9558B335908E16DF1136A7B15"


@pytest.mark.asyncio(loop_scope="session")
class TestDemo:
    async def test_demo(self, client: Client):
        # Create issuer private key and register Hedera DID
        issuer_private_key = PrivateKey.generate_ed25519()
        issuer_did = HederaDid(client=client, private_key_der=issuer_private_key.to_string())

        await issuer_did.register()

        assert issuer_did.topic_id
        assert issuer_did.identifier

        print(
            f"Issuer DID has been registered, see HCS topic details: https://hashscan.io/testnet/topic/{issuer_did.topic_id}"
        )

        # Add DID Document service
        await issuer_did.add_or_update_service(
            id_=f"{issuer_did.identifier}#service-1",
            service_type="LinkedDomains",
            service_endpoint="https://example.com/vcs",
        )

        verification_key = PrivateKey.generate_ed25519()

        # Add DID Document Verification Method
        await issuer_did.add_or_update_verification_method(
            id_=f"{issuer_did.identifier}#key-1",
            controller=issuer_did.identifier,
            public_key_der=verification_key.public_key().to_string(),
            type_=get_key_type(verification_key),
        )

        print(
            "Created DID Service and Verification Method for issuer DID document, waiting for until changes are propagated..."
        )

        # Wait until changes are propagated to Hedera Mirror node
        await asyncio.sleep(5)

        # Create Hedera DID resolver instance
        did_resolver = HederaDidResolver(client)

        print("Resolving issuer DID document...")

        did_resolution_result = await did_resolver.resolve(issuer_did.identifier)
        did_document = did_resolution_result.get("didDocument")

        assert did_document

        print("Resolved issuer DID document:")
        print(json.dumps(did_document, indent=2, default=str))

        # Create Hedera AnonCreds registry instance
        anoncreds_registry = HederaAnonCredsRegistry(client)

        # AnonCreds schema write/read flow

        schema = AnonCredsSchema(
            issuer_id=issuer_did.identifier, name="Demo AnonCreds schema", attr_names=["name", "age"], version="1.0"
        )

        print("Registering AnonCreds schema...")

        schema_registration_result = await anoncreds_registry.register_schema(schema, issuer_private_key.to_string())
        assert schema_registration_result.schema_state.state == "finished"

        schema_identifier = schema_registration_result.schema_state.schema_id
        assert schema_identifier

        schema_topic_id = parse_anoncreds_identifier(schema_identifier).topic_id

        print(
            f"AnonCreds schema has been registered, see HCS topic details: https://hashscan.io/testnet/topic/{schema_topic_id}"
        )
        print(
            f"Schema HCS-1 file can be viewed via KiloScribe CDN API: https://kiloscribe.com/api/inscription-cdn/{schema_topic_id}?network=testnet"
        )

        # Wait until changes are propagated to Hedera Mirror node
        await asyncio.sleep(5)

        print("Resolving schema object...")

        schema_resolution_result = await anoncreds_registry.get_schema(schema_identifier)
        assert schema_resolution_result.schema

        print("Resolved schema object:")
        print(json.dumps(schema_resolution_result.schema.get_json_payload(), indent=2, default=str))

        # AnonCreds credential definition write/read flow

        cred_def = AnonCredsCredDef(
            issuer_id=issuer_did.identifier,
            schema_id=schema_identifier,
            value=CredDefValue(DEMO_CRED_DEF_VALUE_PRIMARY, DEMO_CRED_DEF_VALUE_REVOCATION),
            tag="demo-cred-def-1.0",
        )

        print("Registering AnonCreds credential definition...")

        cred_def_registration_result = await anoncreds_registry.register_cred_def(
            cred_def, issuer_private_key.to_string()
        )
        assert cred_def_registration_result.credential_definition_state.state == "finished"

        cred_def_identifier = cred_def_registration_result.credential_definition_state.credential_definition_id
        assert cred_def_identifier

        cred_def_topic_id = parse_anoncreds_identifier(cred_def_identifier).topic_id

        print(
            f"AnonCreds credential definition has been registered, see HCS topic details: https://hashscan.io/testnet/topic/{cred_def_topic_id}"
        )
        print(
            f"Credential definition HCS-1 file can be viewed via KiloScribe CDN API: https://kiloscribe.com/api/inscription-cdn/{cred_def_topic_id}?network=testnet"
        )

        # Wait until changes are propagated to Hedera Mirror node
        await asyncio.sleep(5)

        print("Resolving credential definition object...")

        cred_def_resolution_result = await anoncreds_registry.get_cred_def(cred_def_identifier)
        assert cred_def_resolution_result.credential_definition

        print("Resolved credential definition object:")
        print(json.dumps(cred_def_resolution_result.credential_definition.get_json_payload(), indent=2, default=str))

        # AnonCreds revocation registry definition write/read flow

        rev_reg_def = AnonCredsRevRegDef(
            issuer_id=issuer_did.identifier,
            cred_def_id=cred_def_identifier,
            value=DEMO_REV_REG_DEF_VALUE,
            tag="demo-rev-reg-1.0",
        )

        print("Registering AnonCreds revocation registry...")

        rev_reg_def_registration_result = await anoncreds_registry.register_rev_reg_def(
            rev_reg_def, issuer_private_key.to_string()
        )
        assert rev_reg_def_registration_result.revocation_registry_definition_state.state == "finished"

        rev_reg_def_identifier = (
            rev_reg_def_registration_result.revocation_registry_definition_state.revocation_registry_definition_id
        )
        assert rev_reg_def_identifier

        rev_reg_def_topic_id = parse_anoncreds_identifier(rev_reg_def_identifier).topic_id

        print(
            f"AnonCreds revocation registry definition has been registered, see HCS topic details: https://hashscan.io/testnet/topic/{rev_reg_def_topic_id}"
        )
        print(
            f"Revocation registry definition HCS-1 file can be viewed via KiloScribe CDN API: https://kiloscribe.com/api/inscription-cdn/{rev_reg_def_topic_id}?network=testnet"
        )

        rev_reg_entries_topic_id = rev_reg_def_registration_result.revocation_registry_definition_metadata.get(
            "entriesTopicId"
        )
        assert rev_reg_entries_topic_id

        print(
            f"Revocation registry entries HCS topic details: https://hashscan.io/testnet/topic/{rev_reg_entries_topic_id}"
        )

        # Wait until changes are propagated to Hedera Mirror node
        await asyncio.sleep(5)

        print("Resolving revocation registry definition object...")

        rev_reg_def_resolution_result = await anoncreds_registry.get_rev_reg_def(rev_reg_def_identifier)
        assert rev_reg_def_resolution_result.revocation_registry_definition

        print("Resolved revocation registry definition object:")
        print(
            json.dumps(
                rev_reg_def_resolution_result.revocation_registry_definition.get_json_payload(), indent=2, default=str
            )
        )

        # Revocation list write/read flow

        rev_list = AnonCredsRevList(
            issuer_id=issuer_did.identifier,
            rev_reg_def_id=rev_reg_def_identifier,
            revocation_list=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            current_accumulator=DEMO_REV_LIST_ACCUM,
        )

        print("Registering AnonCreds revocation list...")

        rev_list_registration_result = await anoncreds_registry.register_rev_list(
            rev_list, issuer_private_key.to_string()
        )
        assert rev_list_registration_result.revocation_list_state.state == "finished"

        rev_list_timestamp = int(time.time())

        # Wait until changes are propagated to Hedera Mirror node
        await asyncio.sleep(5)

        print(
            f"Revocation list has been registered, initial revocation entry can be found in HCS topic: https://hashscan.io/testnet/topic/{rev_reg_entries_topic_id}"
        )

        updated_rev_list = AnonCredsRevList(
            issuer_id=issuer_did.identifier,
            rev_reg_def_id=rev_reg_def_identifier,
            revocation_list=[1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            current_accumulator=DEMO_REV_LIST_ACCUM,
        )

        print("Updating revocation list state...")

        rev_list_update_result = await anoncreds_registry.update_rev_list(
            prev_list=rev_list,
            curr_list=updated_rev_list,
            revoked=[0, 9],
            issuer_key_der=issuer_private_key.to_string(),
        )
        assert rev_list_update_result.revocation_list_state.state == "finished"

        # Wait until changes are propagated to Hedera Mirror node
        await asyncio.sleep(5)

        print("Resolving revocation list states...")

        updated_rev_list_resolution_result = await anoncreds_registry.get_rev_list(
            rev_reg_def_identifier, int(time.time())
        )
        assert updated_rev_list_resolution_result.revocation_list

        print("Current revocation list state:")
        print(json.dumps(updated_rev_list_resolution_result.revocation_list.get_json_payload(), indent=2, default=str))

        rev_list_resolution_result = await anoncreds_registry.get_rev_list(rev_reg_def_identifier, rev_list_timestamp)
        assert rev_list_resolution_result.revocation_list

        print("Initial revocation list state:")
        print(json.dumps(rev_list_resolution_result.revocation_list.get_json_payload(), indent=2, default=str))
