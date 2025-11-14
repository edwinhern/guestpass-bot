"""Discord notification helper for scheduler tasks."""

import logging

import discord

from src.models.registration import Registration

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Helper class for sending Discord notifications."""

    def __init__(self, bot: discord.Client) -> None:
        """Initialize notifier with bot instance."""
        self.bot = bot

    async def send_dm(self, discord_user_id: str, embed: discord.Embed) -> bool:
        """
        Send a DM to a user.

        Returns True if successful, False otherwise.
        """
        try:
            user = await self.bot.fetch_user(int(discord_user_id))
            if not user:
                logger.warning(f"User {discord_user_id} not found")
                return False

            await user.send(embed=embed)
            logger.info(f"Sent DM to user {discord_user_id}")
            return True

        except discord.Forbidden:
            logger.warning(f"Cannot send DM to user {discord_user_id} - DMs disabled")
            return False
        except Exception:
            logger.exception(f"Error sending DM to user {discord_user_id}")
            return False

    async def notify_expiring_soon(self, registration: Registration) -> bool:
        """Send expiration warning notification."""
        embed = discord.Embed(
            title="🟡 Parking Registration Expiring Soon",
            color=discord.Color.orange(),
            description="Your parking registration will expire soon!",
        )

        embed.add_field(name="Guest", value=f"{registration.first_name} {registration.last_name}")
        embed.add_field(
            name="Vehicle",
            value=f"{registration.car_make} {registration.car_model} ({registration.license_plate})",
        )

        if registration.expires_at:
            embed.add_field(name="Expires At", value=registration.expires_at.strftime("%Y-%m-%d %H:%M UTC"))

        embed.add_field(
            name="Action Required",
            value=f"Use `/resubmit {registration.id}` to renew your registration.",
            inline=False,
        )

        return await self.send_dm(registration.discord_user_id, embed)

    async def notify_auto_reregister_success(self, registration: Registration) -> bool:
        """Send auto re-registration success notification."""
        embed = discord.Embed(
            title="✅ Automatic Re-registration Successful",
            color=discord.Color.green(),
            description="Your parking registration has been automatically renewed!",
        )

        embed.add_field(name="Guest", value=f"{registration.first_name} {registration.last_name}")
        embed.add_field(
            name="Vehicle",
            value=f"{registration.car_make} {registration.car_model} ({registration.license_plate})",
        )

        if registration.expires_at:
            embed.add_field(name="New Expiration", value=registration.expires_at.strftime("%Y-%m-%d %H:%M UTC"))

        embed.add_field(name="Submission Count", value=str(registration.submission_count))

        return await self.send_dm(registration.discord_user_id, embed)

    async def notify_auto_reregister_failed(self, registration: Registration, error: str) -> bool:
        """Send auto re-registration failure notification."""
        embed = discord.Embed(
            title="❌ Automatic Re-registration Failed",
            color=discord.Color.red(),
            description="Failed to automatically renew your parking registration.",
        )

        embed.add_field(name="Guest", value=f"{registration.first_name} {registration.last_name}")
        embed.add_field(
            name="Vehicle",
            value=f"{registration.car_make} {registration.car_model} ({registration.license_plate})",
        )

        embed.add_field(name="Error", value=error, inline=False)
        embed.add_field(
            name="Action Required",
            value=f"Please manually resubmit using `/resubmit {registration.id}`",
            inline=False,
        )

        return await self.send_dm(registration.discord_user_id, embed)

    async def notify_expired(self, registration: Registration) -> bool:
        """Send expiration notification."""
        embed = discord.Embed(
            title="🔴 Parking Registration Expired",
            color=discord.Color.red(),
            description="Your parking registration has expired!",
        )

        embed.add_field(name="Guest", value=f"{registration.first_name} {registration.last_name}")
        embed.add_field(
            name="Vehicle",
            value=f"{registration.car_make} {registration.car_model} ({registration.license_plate})",
        )

        embed.add_field(
            name="Action Required",
            value=f"Use `/resubmit {registration.id}` to renew your registration immediately.",
            inline=False,
        )

        return await self.send_dm(registration.discord_user_id, embed)
