# Guest Pass Bot 🚗

A Discord bot that automates guest parking registration for apartment complexes using [Parking Permits of America (PPOA)](https://www.parkingpermitsofamerica.com). Save guest information and quickly resubmit registrations without manually filling out forms repeatedly.

## Features

- ✅ **Automated Registration**: Submit parking registrations to PPOA via Discord
- 💾 **Guest Database**: Store guest information for easy resubmission
- 🔍 **Smart Search**: Find registrations by name, car model, or license plate
- ⏰ **Expiration Tracking**: Get notified before registrations expire (24hr passes)
- 🔄 **Auto Re-registration**: Automatically renew registrations for active guests
- 👥 **Multi-user Support**: Each Discord user manages their own guests
- 🛡️ **Admin Controls**: Admin-only commands for statistics and monitoring

## Architecture

``` txt
Discord Bot → PostgreSQL Database → Playwright Automation → PPOA Website
             ↓
       Background Scheduler (Notifications + Auto Re-registration)
```

**Tech Stack:**

- Python 3.13
- discord.py (Discord bot framework)
- SQLAlchemy Core (database layer)
- PostgreSQL (data storage)
- Flyway (database migrations)
- Playwright (browser automation)
- APScheduler (background tasks)
- Docker & Docker Compose (containerization)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Discord Bot Token ([Create one here](https://discord.com/developers/applications))
- PPOA Registration Code (from your apartment complex)

### 1. Start the Bot

```bash
# Start all services (PostgreSQL, Flyway, Bot)
docker-compose up -d

```

### 2. Invite Bot to Discord

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. Go to OAuth2 → URL Generator
4. Select scopes: `bot`, `applications.commands`
5. Select bot permissions: `Send Messages`, `Use Slash Commands`, `Send Messages in Threads`
6. Copy and open the generated URL to invite the bot

## Discord Commands

### User Commands

| Command | Description |
|---------|-------------|
| `/register` | Register a new guest parking pass (multi-step form) |
| `/myregistrations` | View all your saved registrations |
| `/search <query>` | Search your registrations by name, model, or plate |
| `/resubmit <id>` | Resubmit an existing registration to PPOA |
| `/activate <id>` | Mark a guest as currently staying (enables auto-reregister) |
| `/deactivate <id>` | Mark a guest as not staying (disables auto-reregister) |
| `/toggle-auto <id> <enabled>` | Enable/disable automatic re-registration |

### Admin Commands

| Command | Description |
|---------|-------------|
| `/admin-search <query>` | Search all registrations across users |
| `/admin-stats` | View usage statistics |
| `/admin-active` | List all active registrations with auto-reregister |
| `/admin-expiring <hours>` | View registrations expiring soon |

## Registration Flow

1. **User runs `/register`**
   - Fills out 3-step form (personal info, vehicle details, visit info)

2. **Bot saves to database**
   - Stores all information with Discord user ID

3. **Bot submits to PPOA**
   - Uses Playwright to automate form submission
   - Updates expiration time (24 hours from submission)

4. **Background Tasks**
   - **Expiration Notifications**: Sends DM 2 hours before expiry
   - **Auto Re-registration**: Automatically renews active guests before expiration
