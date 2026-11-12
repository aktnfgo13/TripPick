from pathlib import Path
from typing import Protocol
from uuid import UUID, uuid4


class ObjectStore(Protocol):
    def put(self, data: bytes) -> UUID: ...
    def read(self, key: UUID) -> bytes: ...
    def discard(self, key: UUID) -> None: ...


class LocalObjects:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(mode=0o700, parents=True, exist_ok=True)

    def put(self, data: bytes) -> UUID:
        key = uuid4()
        path = self.root / str(key)
        try:
            with path.open("xb") as stream:
                stream.write(data)
        except FileExistsError:
            raise
        except OSError:
            path.unlink(missing_ok=True)
            raise
        return key

    def read(self, key: UUID) -> bytes:
        return (self.root / str(UUID(str(key)))).read_bytes()

    def discard(self, key: UUID) -> None:
        (self.root / str(UUID(str(key)))).unlink(missing_ok=True)
