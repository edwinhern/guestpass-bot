"""Repository for registration database operations."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import and_, delete, func, insert, or_, select, update

from src.models.base import engine
from src.models.registration import Registration, registrations_table


class RegistrationRepository:
    """Data access layer for registrations."""

    def create(
        self,
        discord_user_id: str,
        first_name: str,
        last_name: str,
        license_plate: str,
        license_plate_state: str,
        car_year: str,
        car_make: str,
        car_model: str,
        car_color: str,
        resident_visiting: str,
        apartment_visiting: str,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Registration:
        """Create a new registration."""
        with engine.begin() as conn:
            stmt = insert(registrations_table).values(
                discord_user_id=discord_user_id,
                first_name=first_name,
                last_name=last_name,
                license_plate=license_plate,
                license_plate_state=license_plate_state,
                car_year=car_year,
                car_make=car_make,
                car_model=car_model,
                car_color=car_color,
                resident_visiting=resident_visiting,
                apartment_visiting=apartment_visiting,
                phone_number=phone_number,
                email=email,
                created_at=datetime.utcnow(),
            )
            result = conn.execute(stmt)
            registration_id = result.inserted_primary_key[0]

            # Fetch and return the created registration
            return self.get_by_id(registration_id)  # type: ignore[return-value]

    def get_by_id(self, registration_id: int) -> Optional[Registration]:
        """Get registration by ID."""
        with engine.connect() as conn:
            stmt = select(registrations_table).where(registrations_table.c.id == registration_id)
            result = conn.execute(stmt)
            row = result.first()
            return Registration.from_row(row) if row else None

    def get_by_user(self, discord_user_id: str) -> list[Registration]:
        """Get all registrations for a user."""
        with engine.connect() as conn:
            stmt = (
                select(registrations_table)
                .where(registrations_table.c.discord_user_id == discord_user_id)
                .order_by(registrations_table.c.created_at.desc())
            )
            result = conn.execute(stmt)
            return [Registration.from_row(row) for row in result]

    def search(
        self,
        query: str,
        discord_user_id: Optional[str] = None,
    ) -> list[Registration]:
        """
        Search registrations by name, car model, or license plate.

        Args:
            query: Search query (name, car model, or first 3 digits of plate)
            discord_user_id: Optional filter by specific user (for user searches)
        """
        with engine.connect() as conn:
            search_pattern = f"%{query.lower()}%"

            # Build conditions
            conditions = [
                func.lower(registrations_table.c.first_name).like(search_pattern),
                func.lower(registrations_table.c.last_name).like(search_pattern),
                func.lower(registrations_table.c.car_model).like(search_pattern),
                func.lower(registrations_table.c.license_plate).like(search_pattern),
            ]

            stmt = select(registrations_table).where(or_(*conditions))

            # Filter by user if specified (for user searches)
            if discord_user_id:
                stmt = stmt.where(registrations_table.c.discord_user_id == discord_user_id)

            stmt = stmt.order_by(registrations_table.c.created_at.desc())

            result = conn.execute(stmt)
            return [Registration.from_row(row) for row in result]

    def update_submission(
        self,
        registration_id: int,
        last_submitted_at: datetime,
        expires_at: datetime,
    ) -> None:
        """Update submission tracking after successful registration."""
        with engine.begin() as conn:
            stmt = (
                update(registrations_table)
                .where(registrations_table.c.id == registration_id)
                .values(
                    last_submitted_at=last_submitted_at,
                    expires_at=expires_at,
                    submission_count=registrations_table.c.submission_count + 1,
                )
            )
            conn.execute(stmt)

    def update_auto_reregister(self, registration_id: int, enabled: bool) -> None:
        """Toggle auto re-registration for a registration."""
        with engine.begin() as conn:
            stmt = (
                update(registrations_table)
                .where(registrations_table.c.id == registration_id)
                .values(auto_reregister=enabled)
            )
            conn.execute(stmt)

    def update_active_status(self, registration_id: int, is_active: bool) -> None:
        """Update active status of a registration."""
        with engine.begin() as conn:
            stmt = (
                update(registrations_table)
                .where(registrations_table.c.id == registration_id)
                .values(is_active=is_active)
            )
            conn.execute(stmt)

    def get_expiring_soon(self, hours_before: int) -> list[Registration]:
        """Get registrations expiring within specified hours."""
        with engine.connect() as conn:
            now = datetime.utcnow()
            threshold = datetime.utcnow().timestamp() + (hours_before * 3600)

            stmt = select(registrations_table).where(
                and_(
                    registrations_table.c.expires_at.isnot(None),
                    registrations_table.c.expires_at > now,
                    func.extract("epoch", registrations_table.c.expires_at) <= threshold,
                )
            )
            result = conn.execute(stmt)
            return [Registration.from_row(row) for row in result]

    def get_active_with_auto_reregister(self) -> list[Registration]:
        """Get all active registrations with auto-reregister enabled."""
        with engine.connect() as conn:
            stmt = select(registrations_table).where(
                and_(
                    registrations_table.c.is_active.is_(True),
                    registrations_table.c.auto_reregister.is_(True),
                )
            )
            result = conn.execute(stmt)
            return [Registration.from_row(row) for row in result]

    def get_stats(self) -> dict[str, Any]:
        """Get registration statistics."""
        with engine.connect() as conn:
            # Total registrations
            total_stmt = select(func.count()).select_from(registrations_table)
            total = conn.execute(total_stmt).scalar()

            # Active registrations
            active_stmt = (
                select(func.count()).select_from(registrations_table).where(registrations_table.c.is_active.is_(True))
            )
            active = conn.execute(active_stmt).scalar()

            # Auto-reregister enabled
            auto_stmt = (
                select(func.count())
                .select_from(registrations_table)
                .where(registrations_table.c.auto_reregister.is_(True))
            )
            auto_count = conn.execute(auto_stmt).scalar()

            # Total submissions
            submissions_stmt = select(func.sum(registrations_table.c.submission_count)).select_from(registrations_table)
            total_submissions = conn.execute(submissions_stmt).scalar() or 0

            return {
                "total_registrations": total,
                "active_registrations": active,
                "auto_reregister_enabled": auto_count,
                "total_submissions": total_submissions,
            }

    def delete(self, registration_id: int) -> bool:
        """Delete a registration."""
        with engine.begin() as conn:
            stmt = delete(registrations_table).where(registrations_table.c.id == registration_id)
            result = conn.execute(stmt)
            return result.rowcount > 0
