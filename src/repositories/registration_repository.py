from datetime import datetime
from typing import Any, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from src.models.registration import Registration


class RegistrationRepository:
    def __init__(self, session: Session) -> None:
        """Initialize the registration repository."""
        self.session = session

    def create(self, registration: Registration) -> Registration:
        """Create a new registration from a Registration object."""
        # Set created_at if not already set
        if not registration.created_at:
            registration.created_at = datetime.utcnow()

        self.session.add(registration)
        self.session.commit()
        self.session.refresh(registration)
        return registration

    def get_by_id(self, registration_id: int) -> Optional[Registration]:
        """Get registration by ID."""
        return self.session.query(Registration).filter(Registration.id == registration_id).first()

    def get_by_user(self, discord_user_id: str) -> list[Registration]:
        """Get all registrations for a user."""
        return (
            self.session.query(Registration)
            .filter(Registration.discord_user_id == discord_user_id)
            .order_by(Registration.created_at.desc())
            .all()
        )

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
        search_pattern = f"%{query.lower()}%"

        # Build conditions
        conditions = or_(
            func.lower(Registration.first_name).like(search_pattern),
            func.lower(Registration.last_name).like(search_pattern),
            func.lower(Registration.car_model).like(search_pattern),
            func.lower(Registration.license_plate).like(search_pattern),
        )

        query_obj = self.session.query(Registration).filter(conditions)

        # Filter by user if specified (for user searches)
        if discord_user_id:
            query_obj = query_obj.filter(Registration.discord_user_id == discord_user_id)

        return query_obj.order_by(Registration.created_at.desc()).all()

    def update_submission(
        self,
        registration_id: int,
        last_submitted_at: datetime,
        expires_at: datetime,
    ) -> None:
        """Update submission tracking after successful registration."""
        registration = self.get_by_id(registration_id)
        if registration:
            registration.last_submitted_at = last_submitted_at
            registration.expires_at = expires_at
            registration.submission_count += 1
            self.session.commit()

    def update_auto_reregister(self, registration_id: int, enabled: bool) -> None:
        """Toggle auto re-registration for a registration."""
        registration = self.get_by_id(registration_id)
        if registration:
            registration.auto_reregister = enabled
            self.session.commit()

    def update_active_status(self, registration_id: int, is_active: bool) -> None:
        """Update active status of a registration."""
        registration = self.get_by_id(registration_id)
        if registration:
            registration.is_active = is_active
            self.session.commit()

    def get_expiring_soon(self, hours_before: int) -> list[Registration]:
        """Get registrations expiring within specified hours."""
        now = datetime.utcnow()
        threshold = datetime.utcnow().timestamp() + (hours_before * 3600)

        return (
            self.session.query(Registration)
            .filter(
                and_(
                    Registration.expires_at.isnot(None),
                    Registration.expires_at > now,
                    func.extract("epoch", Registration.expires_at) <= threshold,
                )
            )
            .all()
        )

    def get_active_with_auto_reregister(self) -> list[Registration]:
        """Get all active registrations with auto-reregister enabled."""
        return (
            self.session.query(Registration)
            .filter(
                and_(
                    Registration.is_active.is_(True),
                    Registration.auto_reregister.is_(True),
                )
            )
            .all()
        )

    def get_stats(self) -> dict[str, Any]:
        """Get registration statistics."""
        # Total registrations
        total = self.session.query(func.count(Registration.id)).scalar()

        # Active registrations
        active = self.session.query(func.count(Registration.id)).filter(Registration.is_active.is_(True)).scalar()

        # Auto-reregister enabled
        auto_count = (
            self.session.query(func.count(Registration.id)).filter(Registration.auto_reregister.is_(True)).scalar()
        )

        # Total submissions
        total_submissions = self.session.query(func.sum(Registration.submission_count)).scalar() or 0

        return {
            "total_registrations": total,
            "active_registrations": active,
            "auto_reregister_enabled": auto_count,
            "total_submissions": total_submissions,
        }

    def delete(self, registration_id: int) -> bool:
        """Delete a registration."""
        registration = self.get_by_id(registration_id)
        if registration:
            self.session.delete(registration)
            self.session.commit()
            return True

        return False
