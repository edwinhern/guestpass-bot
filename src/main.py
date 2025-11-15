"""Main entry point for the Guest Pass Bot."""

import asyncio
import logging
import sys

import discord
from discord.ext import commands

from src.config import config
from src.scheduler.tasks import SchedulerTasks

# Configure logging
logging.basicConfig(
    level=logging.INFO if config.environment == "production" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("guestpass_bot.log") if config.environment == "production" else logging.NullHandler(),
    ],
)

logger = logging.getLogger(__name__)


class GuestPassBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix="!",  # Prefix for traditional commands (not used, but required)
            intents=intents,
            application_id=None,
        )

        self.scheduler: SchedulerTasks = None  # type: ignore[assignment]

    async def setup_hook(self) -> None:
        """Async setup - load cogs and initialize services."""
        logger.info("Loading cogs...")

        # Load event handlers
        await self.load_extension("src.bot.events")

        # Load user commands
        await self.load_extension("src.bot.commands")

        # Load admin commands
        await self.load_extension("src.bot.admin_commands")

        logger.info("All cogs loaded successfully")

        # Initialize scheduler
        logger.info("Initializing scheduler...")
        self.scheduler = SchedulerTasks(self)
        self.scheduler.start()
        logger.info("Scheduler started")

    async def on_ready(self) -> None:
        """Called when bot is fully ready."""
        logger.info(f"Bot is ready! Logged in as {self.user}")
        logger.info(f"Connected to {len(self.guilds)} guilds")

        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="parking registrations",
            )
        )

    async def close(self) -> None:
        """Cleanup when bot shuts down."""
        logger.info("Shutting down bot...")

        if self.scheduler:
            logger.info("Stopping scheduler...")
            self.scheduler.stop()

        await super().close()
        logger.info("Bot shutdown complete")


async def main() -> None:
    """Main function to run the bot."""
    # Validate configuration
    if not config.discord.bot_token:
        logger.error("DISCORD_BOT_TOKEN not set in environment")
        sys.exit(1)

    if not config.database.password:
        logger.error("POSTGRES_PASSWORD not set in environment")
        sys.exit(1)

    logger.info("Starting Guest Pass Bot...")
    logger.info(f"Environment: {config.environment}")
    logger.info(f"Database: {config.database.host}:{config.database.port}/{config.database.database}")

    # Create and run bot
    bot = GuestPassBot()

    try:
        await bot.start(config.discord.bot_token)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        await bot.close()
    except Exception:
        logger.exception("Fatal error")
        await bot.close()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
