from abc import ABC
from dataclasses import dataclass
from typing import ClassVar

from ....utils.serializable import Serializable
from .hcs_did_event_target import HcsDidEventTarget


@dataclass
class HcsDidEvent(ABC, Serializable):
    event_target: ClassVar[HcsDidEventTarget]
