from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, true
from sqlalchemy.orm import Mapped, mapped_column

class HistoryEntryMixin:
    start_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    end_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    is_forgotten: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=true(),
    )
    settled_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
    )
