from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Iterable, Iterator, Protocol, Union


class Effective(Protocol):
    effectivity: "TimeRange"

    def __contains__(self, other: "Effective") -> bool:
        return other.effectivity in self.effectivity

    def is_effective_on(self, time_point: "TimePoint") -> bool:
        return time_point in self.effectivity

    def overlap_with(self, other: "Effective") -> bool:
        return self.effectivity.overlap_with(other.effectivity)

    def adjacent_to(self, other: "Effective") -> bool:
        return self.effectivity.adjacent_to(other.effectivity)


@dataclass(frozen=True)
class TimeRange:
    start: "TimePoint" = field(default_factory=lambda: TimePoint.min())
    end: "TimePoint" = field(default_factory=lambda: TimePoint.max())

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError(
                "Empty time range: 'r.start' must always be before 'r.end'"
            )

    def __repr__(self) -> str:
        return f"[{repr(self.start)}, {repr(self.end)}]"

    def __lt__(self, other: "TimeRange") -> bool:
        return self.end < other.start

    def __gt__(self, other: "TimeRange") -> bool:
        return self.start > other.end

    def __contains__(self, other: Union["TimePoint", "TimeRange"]) -> bool:
        if isinstance(other, TimePoint):
            return self.start <= other <= self.end
        elif isinstance(other, TimeRange):
            return other.included_in(self)
        else:
            return False

    def included_in(self, other: "TimeRange") -> bool:
        return other.start <= self.start and self.end <= other.end

    def overlap_with(self, other: "TimeRange") -> bool:
        return self.start <= other.end and self.end >= other.start

    def adjacent_to(self, other: "TimeRange") -> bool:
        if self < other:
            return self.end.next() == other.start
        elif other < self:
            return other.end.next() == self.start
        else:
            return False

    def intersection(self, other: "TimeRange") -> "TimeRange":
        assert self.overlap_with(other)

        return TimeRange(
            start=max(self.start, other.start),
            end=min(self.end, other.end),
        )

    def union(self, other: "TimeRange") -> "TimeRange":
        assert self.adjacent_to(other) or self.overlap_with(other)

        return TimeRange(
            start=min(self.start, other.start),
            end=max(self.end, other.end),
        )

    def subtract(self, other: "TimeRange") -> Iterator["TimeRange"]:
        if not self.overlap_with(other=other):
            yield self
        else:
            if self.start < other.start:
                yield TimeRange(start=self.start, end=other.start.prev())

            if self.end > other.end:
                yield TimeRange(start=other.end.next(), end=self.end)

    def subtract_all(self, others: Iterable["TimeRange"]) -> list["TimeRange"]:
        to_split_time_ranges = {self}
        while to_split_time_ranges:
            newly_split_time_ranges = {
                split_time_range
                for to_split_time_range in to_split_time_ranges
                for other in others
                for split_time_range in to_split_time_range.subtract(other)
            }

            # We're "stable", nothing more will be split
            if newly_split_time_ranges == to_split_time_ranges:
                break

            to_split_time_ranges = newly_split_time_ranges

        return list(to_split_time_ranges)

    @classmethod
    def from_dates(cls, start: date, end: date) -> "TimeRange":
        start_time = datetime(
            year=start.year,
            month=start.month,
            day=start.day,
            hour=0,
            minute=0,
            second=0,
        )
        end_time = datetime(
            year=end.year,
            month=end.month,
            day=end.day,
            hour=23,
            minute=59,
            second=59,
        )
        return cls(start=TimePoint(start_time), end=TimePoint(end_time))


class TimePoint:
    def __init__(self, d: datetime | date) -> None:
        if isinstance(d, datetime):
            self._datetime: datetime = d.replace(microsecond=0)
        else:
            self._datetime: datetime = datetime(year=d.year, month=d.month, day=d.day)

    @classmethod
    def max(cls) -> "TimePoint":
        if not hasattr(cls, "_max"):
            cls._max = cls(datetime.max)
        return cls._max

    @classmethod
    def min(cls) -> "TimePoint":
        if not hasattr(cls, "_min"):
            cls._min = cls(datetime.min)
        return cls._min

    @classmethod
    def now(cls) -> "TimePoint":
        return cls(datetime.utcnow())

    def next(self) -> "TimePoint":
        return TimePoint(self._datetime + timedelta(seconds=1))

    def prev(self) -> "TimePoint":
        return TimePoint(self._datetime - timedelta(seconds=1))

    def add_days(self, days: int) -> "TimePoint":
        return TimePoint(self._datetime + timedelta(days=days))

    def __repr__(self) -> str:
        return self._datetime.isoformat()

    def __hash__(self) -> int:
        return hash(self._datetime)

    def __str__(self) -> str:
        return str(self._datetime)

    def __lt__(self, other: "TimePoint") -> bool:
        return self._datetime < other._datetime

    def __le__(self, other: "TimePoint") -> bool:
        return self._datetime <= other._datetime

    def __eq__(self, other: "TimePoint") -> bool:
        return self._datetime == other._datetime

    def __ne__(self, other: "TimePoint") -> bool:
        return self._datetime != other._datetime

    def __gt__(self, other: "TimePoint") -> bool:
        return self._datetime > other._datetime

    def __ge__(self, other: "TimePoint") -> bool:
        return self._datetime >= other._datetime
