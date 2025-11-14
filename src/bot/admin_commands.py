"""Admin-only Discord slash commands."""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from src.config import config
from src.services.registration_service import RegistrationService

logger = logging.getLogger(__name__)


def is_admin() -> app_commands.check:
    """Check if user has admin role."""

    async def predicate(interaction: discord.Interaction) -> bool:
        """Check if user has admin role."""
        if not interaction.guild:
            return False

        admin_role_id = config.discord.admin_role_id
        if not admin_role_id:
            # If no admin role configured, deny access
            await interaction.response.send_message("Admin role not configured.", ephemeral=True)
            return False

        # Check if user has the admin role
        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            return False

        has_role = any(str(role.id) == admin_role_id for role in member.roles)

        if not has_role:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

        return has_role

    return app_commands.check(predicate)


class AdminCommands(commands.Cog):
    """Admin commands for registration management."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize admin commands cog."""
        self.bot = bot
        self.service = RegistrationService()

    @app_commands.command(name="admin-search", description="[Admin] Search all registrations across users")
    @app_commands.describe(query="Search by name, car model, or license plate")
    @is_admin()
    async def admin_search(self, interaction: discord.Interaction, query: str) -> None:
        """Search all registrations (admin only)."""
        await interaction.response.defer(ephemeral=True)

        try:
            if len(query) < 2:
                await interaction.followup.send("Search query must be at least 2 characters.", ephemeral=True)
                return

            # Search without user filter
            registrations = self.service.search_registrations(query, discord_user_id=None)

            if not registrations:
                await interaction.followup.send(f"No registrations found matching '{query}'.", ephemeral=True)
                return

            # Create embed
            embed = discord.Embed(
                title=f"Admin Search Results for '{query}'",
                color=discord.Color.gold(),
                description=f"Found {len(registrations)} matching registrations",
            )

            for reg in registrations[:10]:  # Limit to 10 for display
                formatted = self.service.format_registration_display(reg)
                # Add Discord user info
                user_info = f"\n  Discord User: <@{reg.discord_user_id}>"
                embed.add_field(
                    name=f"Registration #{reg.id}",
                    value=formatted + user_info,
                    inline=False,
                )

            if len(registrations) > 10:
                embed.set_footer(text=f"Showing first 10 of {len(registrations)} results")

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.exception("Error in admin search")
            await interaction.followup.send(f"Error: {e!s}", ephemeral=True)

    @app_commands.command(name="admin-stats", description="[Admin] View registration statistics")
    @is_admin()
    async def admin_stats(self, interaction: discord.Interaction) -> None:
        """View registration statistics (admin only)."""
        await interaction.response.defer(ephemeral=True)

        try:
            stats = self.service.get_statistics()

            embed = discord.Embed(
                title="📊 Registration Statistics",
                color=discord.Color.blue(),
            )

            embed.add_field(name="Total Registrations", value=str(stats["total_registrations"]), inline=True)
            embed.add_field(name="Active Registrations", value=str(stats["active_registrations"]), inline=True)
            embed.add_field(
                name="Auto-Reregister Enabled",
                value=str(stats["auto_reregister_enabled"]),
                inline=True,
            )
            embed.add_field(
                name="Total Submissions",
                value=str(stats["total_submissions"]),
                inline=True,
            )

            # Calculate average submissions per registration
            if stats["total_registrations"] > 0:
                avg_submissions = stats["total_submissions"] / stats["total_registrations"]
                embed.add_field(
                    name="Avg Submissions per Registration",
                    value=f"{avg_submissions:.2f}",
                    inline=True,
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.exception("Error fetching stats")
            await interaction.followup.send(f"Error: {e!s}", ephemeral=True)

    @app_commands.command(name="admin-active", description="[Admin] List all active registrations")
    @is_admin()
    async def admin_active(self, interaction: discord.Interaction) -> None:
        """List all active registrations with auto-reregister enabled (admin only)."""
        await interaction.response.defer(ephemeral=True)

        try:
            registrations = self.service.repository.get_active_with_auto_reregister()

            if not registrations:
                await interaction.followup.send("No active registrations with auto-reregister enabled.", ephemeral=True)
                return

            embed = discord.Embed(
                title="🟢 Active Registrations (Auto-Reregister Enabled)",
                color=discord.Color.green(),
                description=f"Total: {len(registrations)} active registrations",
            )

            for reg in registrations[:15]:  # Limit to 15
                formatted = self.service.format_registration_display(reg)
                user_info = f"\n  Discord User: <@{reg.discord_user_id}>"
                embed.add_field(
                    name=f"Registration #{reg.id}",
                    value=formatted + user_info,
                    inline=False,
                )

            if len(registrations) > 15:
                embed.set_footer(text=f"Showing first 15 of {len(registrations)} active registrations")

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.exception("Error fetching active registrations")
            await interaction.followup.send(f"Error: {e!s}", ephemeral=True)

    @app_commands.command(name="admin-expiring", description="[Admin] View registrations expiring soon")
    @app_commands.describe(hours="Hours before expiry to check (default: 2)")
    @is_admin()
    async def admin_expiring(self, interaction: discord.Interaction, hours: int = 2) -> None:
        """View registrations expiring within specified hours (admin only)."""
        await interaction.response.defer(ephemeral=True)

        try:
            registrations = self.service.get_expiring_registrations(hours)

            if not registrations:
                await interaction.followup.send(f"No registrations expiring within {hours} hours.", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"🟡 Registrations Expiring Within {hours} Hours",
                color=discord.Color.orange(),
                description=f"Found {len(registrations)} expiring registrations",
            )

            for reg in registrations[:15]:
                formatted = self.service.format_registration_display(reg)
                user_info = f"\n  Discord User: <@{reg.discord_user_id}>"
                embed.add_field(
                    name=f"Registration #{reg.id}",
                    value=formatted + user_info,
                    inline=False,
                )

            if len(registrations) > 15:
                embed.set_footer(text=f"Showing first 15 of {len(registrations)} expiring registrations")

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.exception("Error fetching expiring registrations")
            await interaction.followup.send(f"Error: {e!s}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    """Load the admin commands cog."""
    await bot.add_cog(AdminCommands(bot))
