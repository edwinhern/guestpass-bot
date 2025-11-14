"""Service layer for registration business logic."""

from datetime import datetime, timedelta
from typing import Optional

from src.models.registration import Registration
from src.repositories.registration_repository import RegistrationRepository


class RegistrationService:
    """Business logic for managing registrations."""

    def __init__(self) -> None:
        """Initialize service with repository."""
        self.repository = RegistrationRepository()

    def create_registration(
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
        """
        Create a new registration.

        Validates input and creates registration record.
        """
        # Basic validation
        if not all([first_name, last_name, license_plate, license_plate_state]):
            raise ValueError("Required fields cannot be empty")

        # Normalize data
        first_name = first_name.strip().title()
        last_name = last_name.strip().title()
        license_plate = license_plate.strip().upper()
        license_plate_state = license_plate_state.strip().upper()

        return self.repository.create(
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
        )

    def get_user_registrations(self, discord_user_id: str) -> list[Registration]:
        """Get all registrations for a user."""
        return self.repository.get_by_user(discord_user_id)

    def get_registration(self, registration_id: int) -> Optional[Registration]:
        """Get a specific registration."""
        return self.repository.get_by_id(registration_id)

    def search_registrations(
        self,
        query: str,
        discord_user_id: Optional[str] = None,
    ) -> list[Registration]:
        """
        Search registrations by name, car model, or license plate.

        Args:
            query: Search term (name, model, or plate)
            discord_user_id: If provided, only search user's registrations
        """
        if len(query) < 2:
            raise ValueError("Search query must be at least 2 characters")

        return self.repository.search(query, discord_user_id)

    def record_submission(self, registration_id: int) -> Registration:
        """
        Record a successful submission to PPOA.

        Updates last_submitted_at, expires_at (24 hours from now), and increments submission count.
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=24)

        self.repository.update_submission(
            registration_id=registration_id,
            last_submitted_at=now,
            expires_at=expires_at,
        )

        # Return updated registration
        registration = self.repository.get_by_id(registration_id)
        if not registration:
            raise ValueError(f"Registration {registration_id} not found")

        return registration

    def toggle_auto_reregister(self, registration_id: int, enabled: bool) -> Registration:
        """Toggle auto re-registration for a registration."""
        self.repository.update_auto_reregister(registration_id, enabled)

        registration = self.repository.get_by_id(registration_id)
        if not registration:
            raise ValueError(f"Registration {registration_id} not found")

        return registration

    def set_active_status(self, registration_id: int, is_active: bool) -> Registration:
        """Set active status for a registration."""
        self.repository.update_active_status(registration_id, is_active)

        registration = self.repository.get_by_id(registration_id)
        if not registration:
            raise ValueError(f"Registration {registration_id} not found")

        return registration

    def get_expiring_registrations(self, hours_before: int = 2) -> list[Registration]:
        """Get registrations that will expire within specified hours."""
        return self.repository.get_expiring_soon(hours_before)

    def get_registrations_for_auto_reregister(
        self,
        hours_before_expiry: int = 2,
    ) -> list[Registration]:
        """
        Get registrations that should be auto-reregistered.

        Returns active registrations with auto-reregister enabled that are expiring soon.
        """
        active_auto = self.repository.get_active_with_auto_reregister()

        # Filter to only those expiring within threshold
        now = datetime.utcnow()
        threshold = now + timedelta(hours=hours_before_expiry)

        return [reg for reg in active_auto if reg.expires_at and reg.expires_at <= threshold]

    def verify_ownership(self, registration_id: int, discord_user_id: str) -> bool:
        """Verify that a user owns a registration."""
        registration = self.repository.get_by_id(registration_id)
        if not registration:
            return False
        return registration.discord_user_id == discord_user_id

    def get_statistics(self) -> dict[str, int]:
        """Get registration statistics."""
        return self.repository.get_stats()

    def delete_registration(self, registration_id: int) -> bool:
        """Delete a registration."""
        return self.repository.delete(registration_id)

    def format_registration_display(self, registration: Registration) -> str:
        """Format a registration for display in Discord."""
        status_emoji = "🟢" if not registration.is_expired else "🔴"
        if not registration.is_expired and registration.is_expiring_soon:
            status_emoji = "🟡"

        expires_str = "Never submitted"
        if registration.expires_at:
            expires_str = registration.expires_at.strftime("%Y-%m-%d %H:%M UTC")

        auto_reregister_str = "✓" if registration.auto_reregister else "✗"
        active_str = "✓" if registration.is_active else "✗"

        return (
            f"{status_emoji} **ID: {registration.id}** - "
            f"{registration.first_name} {registration.last_name}\n"
            f"  Vehicle: {registration.car_year} {registration.car_make} {registration.car_model} "
            f"({registration.car_color})\n"
            f"  Plate: {registration.license_plate} ({registration.license_plate_state})\n"
            f"  Visiting: {registration.resident_visiting} - Apt {registration.apartment_visiting}\n"
            f"  Expires: {expires_str}\n"
            f"  Submissions: {registration.submission_count} | "
            f"Auto-Reregister: {auto_reregister_str} | Active: {active_str}"
        )
