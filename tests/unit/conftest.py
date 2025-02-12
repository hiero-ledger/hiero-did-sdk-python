from dataclasses import dataclass

import pytest
from hiero_sdk_python import Client, PrivateKey, PublicKey
from pytest_mock import MockerFixture

from hiero_did_sdk_python.did.types import SupportedKeyType
from hiero_did_sdk_python.utils.cache import MemoryCache

PRIVATE_KEY = PrivateKey.generate_ed25519()


@dataclass
class TestKey:
    public_key: PublicKey
    private_key: PrivateKey
    key_type: SupportedKeyType
    public_key_base58: str
    public_key_base58_multibase: str


@pytest.fixture
def mock_client(mocker: MockerFixture):
    MockHederaClientProvider = mocker.patch("hiero_sdk_python.Client", autospec=Client)
    return MockHederaClientProvider.return_value


@pytest.fixture
def mock_cache_instance(mocker: MockerFixture):
    MockMemoryCache = mocker.patch("hiero_did_sdk_python.utils.cache.Cache", autospec=MemoryCache[str, object])
    return MockMemoryCache.return_value


@pytest.fixture(
    params=[
        TestKey(
            PublicKey.from_string(
                "302a300506032b6570032100f32f7379f50d72ca6d501da611e2723b24528802983d16b5990255419e2eb2db"
            ),
            PrivateKey.from_string(
                "302e020100300506032b657004220420e4f76aa303bfbf350ad080b879173b31977e5661d51ff5932f6597e2bb6680ff"
            ),
            "Ed25519VerificationKey2018",
            "HNJ37tiLbGxD7XPvnTkaZCAV3PCe5P4HJFGMGUkVVZAJ",
            "zHNJ37tiLbGxD7XPvnTkaZCAV3PCe5P4HJFGMGUkVVZAJ",
        ),
    ]
)
def test_key(request):
    return request.param
