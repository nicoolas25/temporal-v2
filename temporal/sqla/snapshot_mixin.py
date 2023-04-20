from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

class SnapshotMixin:
    start_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
