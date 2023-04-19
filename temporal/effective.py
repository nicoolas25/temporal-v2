from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional, Protocol, Union


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

    def subtract_all(self, others: list["TimeRange"]) -> list["TimeRange"]:
        results = []
        points_of_interest = sorted(
            set(
                time_point
                for time_range in others
                for time_point in (time_range.start, time_range.end)
                if time_point in self
            ),
        )
        in_range = self.start if not self.start in points_of_interest else None
        for time_point in points_of_interest:
            if in_range and not time_point.is_min():
                prev_time_point = time_point.prev() 
                if not any(prev_time_point in other for other in others):
                    results.append(TimeRange(start=in_range, end=prev_time_point))
                    in_range = None
            elif not time_point.is_max():
                next_time_point = time_point.next()
                if not any(next_time_point in other for other in others):
                    in_range = next_time_point
        if in_range and not any(self.end in other for other in others):
            results.append(TimeRange(start=in_range, end=self.end))
        return results

    @classmethod
    def from_datetimes(
        cls, start: datetime | None, end: datetime | None
    ) -> "TimeRange":
        if start and end:
            return cls(start=TimePoint(start), end=TimePoint(end))
        elif start and end is None:
            return cls(start=TimePoint(start))
        elif end and start is None:
            return cls(end=TimePoint(end))
        elif start is None and end is None:
            return cls()
        else:
            raise ValueError("Invalid arguments")

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
    def parse(cls, d: datetime | date | None) -> Optional["TimePoint"]:
        if d is None:
            return None
        else:
            return TimePoint(d)

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

    def is_max(self) -> bool:
        return self == TimePoint.max()

    def is_min(self) -> bool:
        return self == TimePoint.min()

    def add_days(self, days: int) -> "TimePoint":
        return TimePoint(self._datetime + timedelta(days=days))

    def to_datetime(self, min_max_as_none: bool = True) -> datetime | None:
        if min_max_as_none and (self == TimePoint.min() or self == TimePoint.max()):
            return None
        else:
            return self._datetime

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
