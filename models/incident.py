from dataclasses import dataclass

from .channel import Channel


@dataclass
class Incident:
    id: str
    name: str
    channel: Channel
