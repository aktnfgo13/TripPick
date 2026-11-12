from pathlib import Path
from typing import Protocol
from uuid import UUID, uuid4


class ObjectStore(Protocol):
    def put(self, data: bytes) -> UUID: ...
    def read(self, key: UUID) -> bytes: ...


class LocalObjects:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(mode=0o700, parents=True, exist_ok=True)

    def put(self, data: bytes) -> UUID:
        key = uuid4()
        (self.root / str(key)).write_bytes(data)
        return key

    def read(self, key: UUID) -> bytes:
        return (self.root / str(UUID(str(key)))).read_bytes()
