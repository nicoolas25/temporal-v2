import threading
from collections import defaultdict
from typing import Protocol


class Lock(Protocol):
    """
    Provides the same API as other locks.

    See threading.Lock or multiprocessing.Lock.
    """

    key: str

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__()

    def acquire(self, blocking: bool = True, timeout: float = -1) -> bool:
        ...

    def release(self) -> None:

        ...


_default_lock_instances: dict[str, threading.Lock] = defaultdict(threading.Lock)


class DefaultLock(Lock):
    def acquire(self, blocking: bool = True, timeout: float = -1) -> bool:
        return _default_lock_instances[self.key].acquire(blocking, timeout)

    def release(self):
        lock = _default_lock_instances[self.key]
        del _default_lock_instances[self.key]
        lock.release()
