from dataclasses import dataclass
from typing import Generic, Iterator, Sequence, TypeVar

from temporal.effective import Effective, TimePoint, TimeRange
from temporal.errors import MalformedPerspectiveError, MissingValueError

T = TypeVar("T")


@dataclass(frozen=True)
class PerspectiveEntry(Effective, Generic[T]):
    effectivity: TimeRange
    value: T


class Perspective(Generic[T]):
    settled_at: TimePoint
    _entries: list[PerspectiveEntry[T]]

    def __init__(
        self, settled_at: TimePoint, entries: Sequence[PerspectiveEntry[T]] = tuple()
    ) -> None:
        super().__init__()

        self.settled_at = settled_at
        self._entries = list(entries)

        # Trust entries' order... but verify.
        for previous_entry, next_entry in zip(self._entries, self._entries[1:]):
            if previous_entry.effectivity.start > next_entry.effectivity.start:
                raise MalformedPerspectiveError(
                    "Entries effectivity's start are expected to be increasing"
                )
            if previous_entry.effectivity.end > next_entry.effectivity.start:
                raise MalformedPerspectiveError(
                    "Entries effectivity are expected to be non-overlapping"
                )

        # Compact entries
        self._compact_entries()

    def __iter__(self) -> Iterator[PerspectiveEntry[T]]:
        for entry in self._entries:
            yield entry

    def fetch(self, at: TimePoint) -> T:
        for entry in reversed(self._entries):
            if at in entry.effectivity:
                return entry.value

        raise MissingValueError(f"No known value found at time")

    def _compact_entries(self) -> None:
        compacted_entries = []
        for entry in self._entries:
            if (
                compacted_entries
                and compacted_entries[-1].adjacent_to(entry)
                and compacted_entries[-1].value == entry.value
            ):
                last_value = compacted_entries.pop()
                compacted_entries.append(
                    PerspectiveEntry(
                        effectivity=last_value.effectivity.union(entry.effectivity),
                        value=entry.value,
                    )
                )
            else:
                compacted_entries.append(entry)

        self._entries = compacted_entries
