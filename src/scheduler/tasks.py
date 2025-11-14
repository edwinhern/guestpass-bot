"""Background scheduler tasks for automated operations."""

import logging

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.config import config
from src.integrations.parking_registration_integration import ParkingRegistrationIntegration
from src.scheduler.notifier import DiscordNotifier
from src.services.registration_service import RegistrationService

logger = logging.getLogger(__name__)


class SchedulerTasks:
    """Background tasks for expiration notifications and auto re-registration."""

    def __init__(self, bot: discord.Client) -> None:
        """Initialize scheduler tasks."""
        self.bot = bot
        self.service = RegistrationService()
        self.integration = ParkingRegistrationIntegration()
        self.notifier = DiscordNotifier(bot)
        self.scheduler = AsyncIOScheduler()

    def start(self) -> None:
        """Start the scheduler."""
        # Expiration notification task (runs every hour)
        self.scheduler.add_job(
            self.check_expiring_registrations,
            "interval",
            hours=1,
            id="expiration_notifications",
        )

        # Auto re-registration task (runs every 22 hours)
        # This ensures registrations are renewed before they expire
        self.scheduler.add_job(
            self.auto_reregister_active,
            "interval",
            hours=22,
            id="auto_reregistration",
        )

        self.scheduler.start()
        logger.info("Scheduler started with expiration notifications and auto re-registration tasks")

    def stop(self) -> None:
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    async def check_expiring_registrations(self) -> None:
        """Check for expiring registrations and send notifications."""
        try:
            logger.info("Checking for expiring registrations...")

            registrations = self.service.get_expiring_registrations(config.notification.hours_before_expiry)

            logger.info(f"Found {len(registrations)} expiring registrations")

            for registration in registrations:
                # Skip if auto-reregister is enabled (will be handled by auto-reregister task)
                if registration.auto_reregister and registration.is_active:
                    logger.info(f"Skipping notification for registration {registration.id} (auto-reregister enabled)")
                    continue

                # Send expiration warning
                success = await self.notifier.notify_expiring_soon(registration)
                if success:
                    logger.info(f"Sent expiration notification for registration {registration.id}")
                else:
                    logger.warning(f"Failed to send expiration notification for registration {registration.id}")

        except Exception:
            logger.exception("Error in expiration notification task")

    async def auto_reregister_active(self) -> None:
        """Automatically re-register active registrations that are expiring soon."""
        try:
            logger.info("Running auto re-registration task...")

            registrations = self.service.get_registrations_for_auto_reregister(
                config.notification.auto_reregister_hours_before_expiry
            )

            logger.info(f"Found {len(registrations)} registrations for auto re-registration")

            for registration in registrations:
                try:
                    logger.info(f"Auto re-registering registration {registration.id}")

                    # Submit to PPOA
                    success, message = self.integration.submit_registration(registration)

                    if success:
                        # Update submission tracking
                        updated_reg = self.service.record_submission(registration.id)  # type: ignore[assignment]

                        # Send success notification
                        await self.notifier.notify_auto_reregister_success(updated_reg)
                        logger.info(f"Successfully auto re-registered registration {registration.id}")
                    else:
                        # Send failure notification
                        await self.notifier.notify_auto_reregister_failed(registration, message)
                        logger.warning(f"Failed to auto re-register registration {registration.id}: {message}")

                except Exception as e:
                    logger.exception(f"Error auto re-registering registration {registration.id}")
                    await self.notifier.notify_auto_reregister_failed(
                        registration,
                        f"System error: {e!s}",
                    )

        except Exception:
            logger.exception("Error in auto re-registration task")
