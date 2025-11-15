"""Discord slash commands for parking registration."""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from src.bot.modals import RegistrationModal
from src.integrations.parking_registration_integration import ParkingRegistrationIntegration
from src.services.registration_service import RegistrationService

logger = logging.getLogger(__name__)


class RegistrationCommands(commands.Cog):
    """User commands for parking registration management."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize commands cog."""
        self.bot = bot
        self.service = RegistrationService()
        self.integration = ParkingRegistrationIntegration()

    @app_commands.command(name="register", description="Register a new guest parking pass")
    async def register(self, interaction: discord.Interaction) -> None:
        """Start the registration process with a multi-step modal."""
        # Send the first modal directly
        modal = RegistrationModal(self.service, self.integration, str(interaction.user.id))
        await interaction.response.send_modal(modal)

    @app_commands.command(name="myregistrations", description="View all your saved registrations")
    async def my_registrations(self, interaction: discord.Interaction) -> None:
        """List all registrations for the user."""
        await interaction.response.defer(ephemeral=True)

        try:
            registrations = self.service.get_user_registrations(str(interaction.user.id))

            if not registrations:
                await interaction.followup.send("You have no saved registrations.", ephemeral=True)
                return

            # Create embed
            embed = discord.Embed(
                title="Your Parking Registrations",
                color=discord.Color.blue(),
                description=f"Total: {len(registrations)} registrations",
            )

            for reg in registrations[:10]:  # Limit to 10 for display
                formatted = self.service.format_registration_display(reg)
                embed.add_field(name=f"Registration #{reg.id}", value=formatted, inline=False)

            if len(registrations) > 10:
                embed.set_footer(text=f"Showing first 10 of {len(registrations)} registrations")

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.exception("Error fetching registrations")
            await interaction.followup.send(f"Error: {e!s}", ephemeral=True)

    @app_commands.command(name="search", description="Search your registrations")
    @app_commands.describe(query="Search by name, car model, or license plate (min 2 characters)")
    async def search(self, interaction: discord.Interaction, query: str) -> None:
        """Search registrations owned by the user."""
        await interaction.response.defer(ephemeral=True)

        try:
            if len(query) < 2:
                await interaction.followup.send("Search query must be at least 2 characters.", ephemeral=True)
                return

            registrations = self.service.search_registrations(query, str(interaction.user.id))

            if not registrations:
                await interaction.followup.send(f"No registrations found matching '{query}'.", ephemeral=True)
                return

            # Create embed
            embed = discord.Embed(
                title=f"Search Results for '{query}'",
                color=discord.Color.green(),
                description=f"Found {len(registrations)} matching registrations",
            )

            for reg in registrations[:5]:  # Limit to 5 for display
                formatted = self.service.format_registration_display(reg)
                embed.add_field(name=f"Registration #{reg.id}", value=formatted, inline=False)

            if len(registrations) > 5:
                embed.set_footer(text=f"Showing first 5 of {len(registrations)} results")

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.exception("Error searching registrations")
            await interaction.followup.send(f"Error: {e!s}", ephemeral=True)

    @app_commands.command(name="resubmit", description="Resubmit an existing registration to PPOA")
    @app_commands.describe(registration_id="The ID of the registration to resubmit")
    async def resubmit(self, interaction: discord.Interaction, registration_id: int) -> None:
        """Resubmit an existing registration."""
        await interaction.response.defer(ephemeral=True)

        try:
            # Verify ownership
            if not self.service.verify_ownership(registration_id, str(interaction.user.id)):
                await interaction.followup.send("Registration not found or you don't own it.", ephemeral=True)
                return

            registration = self.service.get_registration(registration_id)
            if not registration:
                await interaction.followup.send("Registration not found.", ephemeral=True)
                return

            # Submit to PPOA
            await interaction.followup.send("Submitting registration to PPOA...", ephemeral=True)

            success, message = await self.integration.submit_registration(registration)

            if success:
                # Update submission tracking
                updated_reg = self.service.record_submission(registration_id)

                embed = discord.Embed(
                    title="✅ Registration Submitted",
                    color=discord.Color.green(),
                    description=message,
                )
                embed.add_field(
                    name="Expires At",
                    value=updated_reg.expires_at.strftime("%Y-%m-%d %H:%M UTC") if updated_reg.expires_at else "N/A",
                )
                embed.add_field(name="Total Submissions", value=str(updated_reg.submission_count))

                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Submission failed: {message}", ephemeral=True)

        except Exception as e:
            logger.exception("Error resubmitting registration")
            await interaction.followup.send(f"Error: {e!s}", ephemeral=True)

    @app_commands.command(name="activate", description="Mark a registration as active (enables auto-reregister)")
    @app_commands.describe(registration_id="The ID of the registration to activate")
    async def activate(self, interaction: discord.Interaction, registration_id: int) -> None:
        """Activate a registration."""
        await interaction.response.defer(ephemeral=True)

        try:
            if not self.service.verify_ownership(registration_id, str(interaction.user.id)):
                await interaction.followup.send("Registration not found or you don't own it.", ephemeral=True)
                return

            registration = self.service.set_active_status(registration_id, True)

            await interaction.followup.send(
                f"✅ Registration #{registration.id} is now **ACTIVE**\n"
                f"Guest: {registration.first_name} {registration.last_name}\n"
                f"Vehicle: {registration.car_make} {registration.car_model}",
                ephemeral=True,
            )

        except Exception as e:
            logger.exception("Error activating registration")
            await interaction.followup.send(f"Error: {e!s}", ephemeral=True)

    @app_commands.command(name="deactivate", description="Mark a registration as inactive (disables auto-reregister)")
    @app_commands.describe(registration_id="The ID of the registration to deactivate")
    async def deactivate(self, interaction: discord.Interaction, registration_id: int) -> None:
        """Deactivate a registration."""
        await interaction.response.defer(ephemeral=True)

        try:
            if not self.service.verify_ownership(registration_id, str(interaction.user.id)):
                await interaction.followup.send("Registration not found or you don't own it.", ephemeral=True)
                return

            registration = self.service.set_active_status(registration_id, False)

            await interaction.followup.send(
                f"⏸️ Registration #{registration.id} is now **INACTIVE**\n"
                f"Guest: {registration.first_name} {registration.last_name}\n"
                f"Auto-reregister has been disabled.",
                ephemeral=True,
            )

        except Exception as e:
            logger.exception("Error deactivating registration")
            await interaction.followup.send(f"Error: {e!s}", ephemeral=True)

    @app_commands.command(name="toggle-auto", description="Toggle automatic re-registration for a guest")
    @app_commands.describe(
        registration_id="The ID of the registration", enabled="Enable or disable auto re-registration"
    )
    async def toggle_auto(self, interaction: discord.Interaction, registration_id: int, enabled: bool) -> None:
        """Toggle auto re-registration."""
        await interaction.response.defer(ephemeral=True)

        try:
            if not self.service.verify_ownership(registration_id, str(interaction.user.id)):
                await interaction.followup.send("Registration not found or you don't own it.", ephemeral=True)
                return

            registration = self.service.toggle_auto_reregister(registration_id, enabled)

            status = "**ENABLED** ✅" if enabled else "**DISABLED** ❌"
            await interaction.followup.send(
                f"Auto re-registration {status} for Registration #{registration.id}\n"
                f"Guest: {registration.first_name} {registration.last_name}",
                ephemeral=True,
            )

        except Exception as e:
            logger.exception("Error toggling auto-reregister")
            await interaction.followup.send(f"Error: {e!s}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    """Load the registration commands cog."""
    await bot.add_cog(RegistrationCommands(bot))
