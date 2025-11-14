# Setup Guide

This guide will walk you through setting up the Guest Pass Bot locally.

## Prerequisites

- Python 3.13+
- Docker and Docker Compose
- Discord Bot Token
- UV package manager (or pip)

## Step 1: Environment Configuration

Create a `.env` file in the project root (copy from the template below):

```bash
# Database Configuration
POSTGRES_USER=guestpass_user
POSTGRES_PASSWORD=supersecretpassword123
POSTGRES_DB=guestpass_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token_here
ADMIN_ROLE_ID=your_admin_role_id_here

# PPOA Configuration
PPOA_REGISTRATION_CODE=MAVP
DEFAULT_APARTMENT=215

# Notification Settings
NOTIFICATION_HOURS_BEFORE_EXPIRY=2
AUTO_REREGISTER_HOURS_BEFORE_EXPIRY=2

# Environment
ENVIRONMENT=development
```

**Important:** Replace the placeholder values:
- `POSTGRES_PASSWORD`: Choose a strong password
- `DISCORD_BOT_TOKEN`: Your Discord bot token from [Discord Developer Portal](https://discord.com/developers/applications)
- `ADMIN_ROLE_ID`: Discord role ID for admin users

## Step 2: Start PostgreSQL

Start the PostgreSQL database using Docker Compose:

```bash
docker-compose up -d postgres
```

Verify it's running:

```bash
docker-compose ps
```

You should see `guestpass-postgres` with status "Up".

## Step 3: Run Database Migrations

Apply the database schema using Flyway:

```bash
docker-compose up flyway
```

This will create the `registrations` table and indexes.

## Step 4: Install Python Dependencies

Using UV (recommended):

```bash
uv sync
```

Or using pip:

```bash
pip install -e .
```

## Step 5: Test Database Connection

Run the test script to verify everything is set up correctly:

```bash
uv run python test_db.py
```

Expected output:

```
✓ Database connection successful
✓ Registrations table exists (current count: 0)
✓ All database tests passed!
```

## Step 6: Install Playwright Browsers

Playwright requires browser binaries:

```bash
uv run playwright install chromium
```

## Step 7: Run the Bot

Start the Discord bot:

```bash
uv run python -m src.main
```

## Troubleshooting

### Database Connection Failed

- Ensure Docker is running: `docker ps`
- Check PostgreSQL logs: `docker-compose logs postgres`
- Verify `.env` file exists and has correct credentials

### Flyway Migration Failed

- Ensure postgres is healthy: `docker-compose ps`
- Check Flyway logs: `docker-compose logs flyway`
- Try running migrations again: `docker-compose up flyway`

### Bot Won't Start

- Verify `DISCORD_BOT_TOKEN` is set in `.env`
- Check bot has proper permissions in Discord Developer Portal
- Ensure dependencies are installed: `uv sync`

## Next Steps

1. Invite your bot to a Discord server
2. Test `/register` command
3. Configure admin role with `ADMIN_ROLE_ID`
4. Test auto-registration features

## Development Commands

```bash
# Start just PostgreSQL
docker-compose up -d postgres

# Run migrations
docker-compose up flyway

# Stop all services
docker-compose down

# Stop and remove volumes (deletes all data)
docker-compose down -v

# View logs
docker-compose logs -f postgres

# Access PostgreSQL CLI
docker-compose exec postgres psql -U guestpass_user -d guestpass_db
```
