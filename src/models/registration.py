"""Registration model and DTO."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Table

from src.models.base import metadata

# SQLAlchemy Core table definition
registrations_table = Table(
    "registrations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("discord_user_id", String(255), nullable=False, index=True),
    Column("first_name", String(100), nullable=False, index=True),
    Column("last_name", String(100), nullable=False, index=True),
    Column("license_plate", String(20), nullable=False, index=True),
    Column("license_plate_state", String(2), nullable=False),
    Column("car_year", String(4), nullable=False),
    Column("car_make", String(50), nullable=False),
    Column("car_model", String(50), nullable=False, index=True),
    Column("car_color", String(30), nullable=False),
    Column("resident_visiting", String(100), nullable=False),
    Column("apartment_visiting", String(20), nullable=False),
    Column("phone_number", String(20), nullable=True),
    Column("email", String(255), nullable=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    Column("last_submitted_at", DateTime, nullable=True),
    Column("expires_at", DateTime, nullable=True),
    Column("submission_count", Integer, nullable=False, default=0),
    Column("auto_reregister", Boolean, nullable=False, default=False),
    Column("is_active", Boolean, nullable=False, default=False),
)


@dataclass
class Registration:
    """Registration data transfer object."""

    id: Optional[int]
    discord_user_id: str
    first_name: str
    last_name: str
    license_plate: str
    license_plate_state: str
    car_year: str
    car_make: str
    car_model: str
    car_color: str
    resident_visiting: str
    apartment_visiting: str
    phone_number: Optional[str]
    email: Optional[str]
    created_at: datetime
    last_submitted_at: Optional[datetime]
    expires_at: Optional[datetime]
    submission_count: int
    auto_reregister: bool
    is_active: bool

    @classmethod
    def from_row(cls, row: Any) -> "Registration":
        """Create Registration from database row."""
        return cls(
            id=row.id,
            discord_user_id=row.discord_user_id,
            first_name=row.first_name,
            last_name=row.last_name,
            license_plate=row.license_plate,
            license_plate_state=row.license_plate_state,
            car_year=row.car_year,
            car_make=row.car_make,
            car_model=row.car_model,
            car_color=row.car_color,
            resident_visiting=row.resident_visiting,
            apartment_visiting=row.apartment_visiting,
            phone_number=row.phone_number,
            email=row.email,
            created_at=row.created_at,
            last_submitted_at=row.last_submitted_at,
            expires_at=row.expires_at,
            submission_count=row.submission_count,
            auto_reregister=row.auto_reregister,
            is_active=row.is_active,
        )

    @property
    def is_expired(self) -> bool:
        """Check if registration is expired."""
        if self.expires_at is None:
            return True
        return datetime.now(datetime.timezone.utc) >= self.expires_at

    @property
    def is_expiring_soon(self) -> bool:
        """Check if registration is expiring within configured hours."""
        from src.config import config

        if self.expires_at is None:
            return False
        hours_until_expiry = (self.expires_at - datetime.utcnow()).total_seconds() / 3600
        return 0 < hours_until_expiry <= config.notification.hours_before_expiry

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "discord_user_id": self.discord_user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "license_plate": self.license_plate,
            "license_plate_state": self.license_plate_state,
            "car_year": self.car_year,
            "car_make": self.car_make,
            "car_model": self.car_model,
            "car_color": self.car_color,
            "resident_visiting": self.resident_visiting,
            "apartment_visiting": self.apartment_visiting,
            "phone_number": self.phone_number,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_submitted_at": self.last_submitted_at.isoformat() if self.last_submitted_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "submission_count": self.submission_count,
            "auto_reregister": self.auto_reregister,
            "is_active": self.is_active,
        }
