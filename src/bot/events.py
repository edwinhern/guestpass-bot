"""Discord bot event handlers."""

import logging

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class BotEvents(commands.Cog):
    """Event handlers for the Discord bot."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize events cog."""
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Called when bot is ready."""
        logger.info(f"Bot logged in as {self.bot.user}")
        logger.info(f"Connected to {len(self.bot.guilds)} guilds")

        # Sync slash commands
        try:
            synced = await self.bot.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception:
            logger.exception("Failed to sync commands")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            return

        logger.error(f"Command error: {error}")
        await ctx.send(f"An error occurred: {error!s}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Called when bot joins a guild."""
        logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """Called when bot leaves a guild."""
        logger.info(f"Left guild: {guild.name} (ID: {guild.id})")


async def setup(bot: commands.Bot) -> None:
    """Load the events cog."""
    await bot.add_cog(BotEvents(bot))
