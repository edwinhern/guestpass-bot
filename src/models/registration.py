from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Registration(Base):
    __tablename__ = "registrations"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Required fields
    discord_user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    license_plate: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    license_plate_state: Mapped[str] = mapped_column(String(2), nullable=False)
    car_year: Mapped[str] = mapped_column(String(4), nullable=False)
    car_make: Mapped[str] = mapped_column(String(50), nullable=False)
    car_model: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    car_color: Mapped[str] = mapped_column(String(30), nullable=False)
    resident_visiting: Mapped[str] = mapped_column(String(100), nullable=False)
    apartment_visiting: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)

    # Optional fields
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Timestamp fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    last_submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Status fields
    submission_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    auto_reregister: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    @property
    def is_expired(self) -> bool:
        """Check if registration is expired."""
        if self.expires_at is None:
            return True

        # Make expires_at timezone-aware if it's naive
        expires_aware = (
            self.expires_at.replace(tzinfo=timezone.utc) if self.expires_at.tzinfo is None else self.expires_at
        )
        # Compare with timezone-aware current time
        now_aware = datetime.now(timezone.utc)
        return now_aware >= expires_aware

    @property
    def is_expiring_soon(self) -> bool:
        """Check if registration is expiring within configured hours."""
        from src.config import config

        if self.expires_at is None:
            return False

        # Make expires_at timezone-aware if it's naive
        expires_aware = (
            self.expires_at.replace(tzinfo=timezone.utc) if self.expires_at.tzinfo is None else self.expires_at
        )
        # Compare with timezone-aware current time
        now_aware = datetime.now(timezone.utc)
        hours_until_expiry = (expires_aware - now_aware).total_seconds() / 3600
        return 0 < hours_until_expiry <= config.notification.hours_before_expiry
