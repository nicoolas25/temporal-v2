import pytest
from sqlalchemy.orm.session import Session

from temporal.effective import TimePoint, TimeRange
from temporal.errors import MissingValueError
from temporal.tests.models import (Subscription, SubscriptionVersion,
                                   _SubscriptionHistoryEntry)


def test_session(session: Session):
    # We can save things
    new_subscription = Subscription()
    session.add(new_subscription)
    session.commit()

    # We can query things
    saved_subscription = session.query(Subscription).one()

    # We can traverse relationships
    assert saved_subscription == new_subscription
    assert saved_subscription.subscription_history_entries == []

    now = TimePoint.now()
    later = now.add_days(days=2)
    even_later = now.add_days(days=4)

    # No version leads to a MissingValueError
    with pytest.raises(MissingValueError):
        saved_subscription.history.fetch(at=now)

    # Recording a first version starting now
    saved_subscription.history.record("hey", effectivity=TimeRange(start=now))
    assert len(saved_subscription.subscription_history_entries) == 1
    assert len(saved_subscription.subscription_versions) == 1

    # Recording a new piece of knowledge is visible from both the history and the versions
    saved_subscription.history.record("ho", effectivity=TimeRange(start=later))
    assert len(saved_subscription.subscription_history_entries) == 2
    assert len(saved_subscription.subscription_versions) == 2

    # Fixing a mistake adds a history entry but no version
    saved_subscription.history.record("hop", effectivity=TimeRange(start=later))
    assert len(saved_subscription.subscription_history_entries) == 3
    assert len(saved_subscription.subscription_versions) == 2

    # Adding the same value doesn't create a new version that changes nothing
    saved_subscription.history.record("hop", effectivity=TimeRange(start=even_later))
    assert len(saved_subscription.subscription_history_entries) == 4
    assert len(saved_subscription.subscription_versions) == 2

    assert [
        f"{now} 0 hey None",
        f"{later} 1 ho None",
        f"{later} 2 hop None",
        f"{even_later} 3 hop None",
    ] == [
        f"{entry.start_at} {entry.version} {entry.value} {entry.end_at}"
        for entry in session.query(_SubscriptionHistoryEntry)
    ]

    assert [f"{now} hey", f"{later} hop"] == [
        f"{entry.start_at} {entry.value}"
        for entry in session.query(SubscriptionVersion)
    ]
