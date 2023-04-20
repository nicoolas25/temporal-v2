from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from temporal.effective import TimePoint, TimeRange
from temporal.history import History, HistoryEntry
from temporal.perspective import Perspective, Snapshot
from temporal.sqla.history_entry_mixin import HistoryEntryMixin
from temporal.sqla.snapshot_mixin import SnapshotMixin


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)


class Subscription(Base):
    __tablename__ = "subscription"
    __allow_unmapped__ = True

    subscription_history_entries: Mapped[
        list["_SubscriptionHistoryEntry"]
    ] = relationship(
        order_by="_SubscriptionHistoryEntry.version.asc()",
        cascade="all, delete-orphan",
    )

    subscription_versions: Mapped[list["SubscriptionVersion"]] = relationship(
        order_by="SubscriptionVersion.start_at.asc()",
        cascade="all, delete-orphan",
    )

    # Internals
    _history: History[str] | None = None
    _latest_perspective: Perspective[str] | None = None

    @property
    def history(self) -> History[str]:
        if not self._history:
            self._history = History(
                id=str(self.id),
                entries=[
                    HistoryEntry(
                        effectivity=TimeRange.from_datetimes(
                            start=entry.start_at, end=entry.end_at
                        ),
                        settled_at=TimePoint(entry.settled_at),
                        version=entry.version,
                        _value=entry.value,
                        _is_forgotten=entry.is_forgotten,
                    )
                    for entry in self.subscription_history_entries
                ],
                on_record=self._add_history_entry,
            )

        return self._history

    @property
    def latest_perspective(self) -> Perspective[str]:
        if not self._latest_perspective:
            self._latest_perspective = Perspective(
                settled_at=TimePoint.now(),
                entries=[
                    Snapshot(
                        effectivity=TimeRange.from_datetimes(
                            start=version.start_at,
                            end=version.end_at,
                        ),
                        value=version.value,
                    )
                    for version in self.subscription_versions
                ],
            )

        return self._latest_perspective

    def _add_history_entry(self, entry: HistoryEntry[str], history: History[str]):
        # Keep history in sync, since it's happen only, we might get away with this
        # Alternatively, we could rewrite the whole history.
        self.subscription_history_entries.append(
            _SubscriptionHistoryEntry(
                start_at=entry.effectivity.start.to_datetime(),
                end_at=entry.effectivity.end.to_datetime(),
                settled_at=entry.settled_at.to_datetime(),
                version=entry.version,
                is_forgotten=entry._is_forgotten,
                value=entry.get_value_or_none(),
            )
        )

        # Rebuild all subscription_versions
        self.subscription_versions = [
            SubscriptionVersion(
                start_at=entry.effectivity.start.to_datetime(min_max_as_none=False),
                end_at=entry.effectivity.end.to_datetime(min_max_as_none=False),
                value=entry.value,
            )
            for entry in history.get_perspective(settled_at=entry.settled_at)
        ]

        # Invalidate the latest_perspective cache
        self._latest_perspective = None


class SubscriptionVersion(SnapshotMixin, Base):
    """
    Persisted projection of a subscription history using all available knowledge.

    The IDs aren't stable as this is a projection is fully rebuilt. Use something like
    `version_at` if you need to reference a specific version.
    """

    __tablename__ = "subscription_version"

    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("subscription.id"),
        nullable=False,
    )

    # Take a simple value for this example
    value: Mapped[str] = mapped_column(String, nullable=False)


# This is a "private" model as the goal is to never interact it directly.
class _SubscriptionHistoryEntry(HistoryEntryMixin, Base):
    __tablename__ = "subscription_history_entry"

    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("subscription.id"),
        nullable=False,
    )

    # Take a simple value for this example
    value: Mapped[str] = mapped_column(String, nullable=False)
