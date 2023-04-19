from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, true
from sqlalchemy.orm import Mapped, mapped_column

class PerspectiveEntryMixin:
    start_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
