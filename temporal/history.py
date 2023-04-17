from dataclasses import dataclass
from typing import Generic, Iterator, Sequence, TypeVar

from temporal.perspective import Perspective, PerspectiveEntry

from .effective import Effective, TimePoint, TimeRange
from .errors import MalformedHistoryError, MissingValueError

T = TypeVar("T")


@dataclass(frozen=True)
class HistoryEntry(Generic[T], Effective):
    effectivity: TimeRange
    settled_at: TimePoint
    version: int
    _value: T
    _is_forgotten: bool = False

    def get_value(self) -> T:
        if self._is_forgotten:
            raise MissingValueError("No known value at this time")

        return self._value

    def is_empty(self) -> bool:
        return self._is_forgotten


class History(Generic[T]):
    id: str
    _entries: list[HistoryEntry[T]]

    def __init__(
        self,
        id: str,
        entries: Sequence[HistoryEntry[T]] = tuple(),
    ) -> None:
        super().__init__()

        self.id = id
        self._entries = list(entries)

        # Trust entries' order... but verify.
        for previous_entry, next_entry in zip(self._entries, self._entries[1:]):
            if previous_entry.settled_at > next_entry.settled_at:
                raise MalformedHistoryError(
                    "Entries's settled_at are expected be increasing"
                )
            if next_entry.version != previous_entry.version + 1:
                raise MalformedHistoryError(
                    "Entries's version are expected to be following each other"
                )

    def record(
        self,
        value: T,
        effectivity: TimeRange,
        _settled_at: TimePoint | None = None,
    ) -> None:
        """
        Record that value was effective during the effectivity time range.
        """

        self._entries.append(
            HistoryEntry(
                _value=value,
                effectivity=effectivity,
                settled_at=_settled_at or TimePoint.now(),
                version=self._get_next_version(),
            ),
        )

    def forget(
        self,
        effectivity: TimeRange,
        _settled_at: TimePoint | None = None,
    ) -> None:
        self._entries.append(
            HistoryEntry(
                effectivity=effectivity,
                settled_at=_settled_at or TimePoint.now(),
                version=self._get_next_version(),
                _value=None,  # type: ignore
                _is_forgotten=True,
            ),
        )

    def fetch(
        self,
        at: TimePoint,
        settled_at: TimePoint | None = None,
    ) -> T:
        """
        Return the latest known (using settled_at as reference) recorded value at `at` point.

        If settled_at isn't provided, TimePoint.now() is used.
        """

        # NOTE: We look at the latest piece of knowledge we have on the property for that point in time.
        # Since the entries are ordered, we can stop looking at the first matching entry.

        for entry in self._entries_settled_at(settled_at):
            if at in entry.effectivity:
                return entry.get_value()

        raise MissingValueError(f"No known value found at time")

    def get_perspective(
        self,
        settled_at: TimePoint,
    ) -> Perspective[T]:
        projections: list[tuple[TimeRange, T, bool]] = []

        for entry in self._entries_settled_at(settled_at):
            known_time_ranges = [projection[0] for projection in projections]
            for time_range in entry.effectivity.subtract_all(known_time_ranges):
                projections.append((time_range, entry._value, entry.is_empty()))

        return Perspective(
            settled_at=settled_at,
            entries=sorted(
                [
                    PerspectiveEntry(effectivity=projection[0], value=projection[1])
                    for projection in projections
                    if projection[2]
                ],
                key=lambda pe: pe.effectivity.start,
            ),
        )

    def _entries_settled_at(
        self,
        settled_at: TimePoint | None = None,
    ) -> Iterator[HistoryEntry[T]]:
        """
        Yields each HistoryEntry from the most to the least recently settled.
        Entries settled after the provided `settled_at` time are excluded.

        By default, without settled_at, TimePoint.now() is used.
        """
        settled_at = settled_at or TimePoint.now()

        for entry in reversed(self._entries):
            if entry.settled_at > settled_at:
                continue
            yield entry

    def _get_next_version(self) -> int:
        return self._entries[-1].version + 1 if self._entries else 0
