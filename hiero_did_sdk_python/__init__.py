import logging
import os
from typing import get_args

from .anoncreds import (
    AnonCredsCredDef,
    AnonCredsRevList,
    AnonCredsRevRegDef,
    AnonCredsSchema,
    CredDefValue,
    CredDefValuePrimary,
    CredDefValueRevocation,
    HederaAnonCredsRegistry,
    RevRegDefValue,
)
from .did import DidDocument, DidErrorCode, DidException, HederaDid, HederaDidResolver
from .utils.cache import Cache, MemoryCache
from .utils.logger import LogLevel, configure_logger

LOG_LEVEL = os.environ.get("HEDERA_DID_SDK_LOG_LEVEL", None)
LOG_FORMAT = os.environ.get("HEDERA_DID_SDK_LOG_FORMAT", None)

if LOG_LEVEL not in [*get_args(LogLevel), None]:
    raise Exception("Invalid log level")

configure_logger(logging.getLogger(), LOG_LEVEL, LOG_FORMAT)

__all__ = [
    "HederaDidResolver",
    "HederaDid",
    "DidDocument",
    "DidException",
    "DidErrorCode",
    "HederaAnonCredsRegistry",
    "AnonCredsSchema",
    "AnonCredsCredDef",
    "CredDefValue",
    "CredDefValuePrimary",
    "CredDefValueRevocation",
    "AnonCredsRevRegDef",
    "RevRegDefValue",
    "AnonCredsRevList",
    "Cache",
    "MemoryCache",
]
