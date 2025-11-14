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

```
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

### 1. Clone the Repository

```bash
git clone <repository-url>
cd guestpass-bot
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
# Database Configuration
POSTGRES_USER=guestpass_user
POSTGRES_PASSWORD=your_secure_password_here
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

### 3. Start the Bot

```bash
# Start all services (PostgreSQL, Flyway, Bot)
docker-compose up -d

# View logs
docker-compose logs -f bot
```

### 4. Invite Bot to Discord

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

## Database Schema

```sql
CREATE TABLE registrations (
    id SERIAL PRIMARY KEY,
    discord_user_id VARCHAR(255) NOT NULL,

    -- Personal Information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,

    -- Vehicle Information
    license_plate VARCHAR(20) NOT NULL,
    license_plate_state VARCHAR(2) NOT NULL,
    car_year VARCHAR(4) NOT NULL,
    car_make VARCHAR(50) NOT NULL,
    car_model VARCHAR(50) NOT NULL,
    car_color VARCHAR(30) NOT NULL,

    -- Visit Information
    resident_visiting VARCHAR(100) NOT NULL,
    apartment_visiting VARCHAR(20) NOT NULL,

    -- Contact Information
    phone_number VARCHAR(20),
    email VARCHAR(255),

    -- Tracking
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_submitted_at TIMESTAMP,
    expires_at TIMESTAMP,
    submission_count INTEGER NOT NULL DEFAULT 0,
    auto_reregister BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT FALSE
);
```

## Development

### Local Development (Without Docker)

1. **Start PostgreSQL**

   ```bash
   docker-compose up -d postgres
   ```

2. **Run Flyway Migrations**

   ```bash
   docker-compose up flyway
   ```

3. **Install Dependencies**

   ```bash
   uv sync
   ```

4. **Install Playwright Browsers**

   ```bash
   uv run playwright install chromium
   ```

5. **Test Database Connection**

   ```bash
   uv run python test_db.py
   ```

6. **Run Bot**

   ```bash
   uv run python -m src.main
   ```

### Project Structure

```
guestpass-bot/
├── database/
│   ├── migrations/          # Flyway SQL migrations
│   │   └── V1__initial_schema.sql
│   └── flyway.conf
├── src/
│   ├── models/              # Data models and DTOs
│   │   ├── base.py          # SQLAlchemy engine setup
│   │   └── registration.py  # Registration table and DTO
│   ├── repositories/        # Data access layer
│   │   └── registration_repository.py
│   ├── services/            # Business logic
│   │   └── registration_service.py
│   ├── integrations/        # External integrations
│   │   └── parking_registration_integration.py
│   ├── bot/                 # Discord bot
│   │   ├── commands.py      # User commands
│   │   ├── admin_commands.py # Admin commands
│   │   ├── modals.py        # Discord modals
│   │   └── events.py        # Event handlers
│   ├── scheduler/           # Background tasks
│   │   ├── tasks.py         # Scheduler tasks
│   │   └── notifier.py      # Discord notifications
│   ├── config.py            # Configuration management
│   └── main.py              # Entry point
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

### Running Tests

```bash
# Test database connection
uv run python test_db.py

# Test Playwright integration (manual verification)
# The bot logs will show submission attempts
```

## Deployment

### Cloud Deployment (Railway/Render)

1. **Set up PostgreSQL database** on your cloud platform

2. **Configure environment variables** in platform settings

3. **Deploy via Docker**
   - Most platforms auto-detect Dockerfile
   - Or use `docker-compose.yml` for multi-service deployment

4. **Run Flyway migrations**

   ```bash
   # One-time migration setup
   docker-compose up flyway
   ```

5. **Monitor logs** for startup confirmation

### Self-hosted with Cloudflare Tunnel

1. **Run on local server**

   ```bash
   docker-compose up -d
   ```

2. **Set up Cloudflare Tunnel** (optional, for web dashboard later)

   ```bash
   cloudflared tunnel create guestpass-bot
   cloudflared tunnel route dns guestpass-bot guestpass.yourdomain.com
   ```

## Configuration

### Discord Bot Permissions

Required bot permissions:

- `Send Messages`
- `Use Slash Commands`
- `Send Messages in Threads`
- `Read Message History`

### Getting Admin Role ID

1. Enable Developer Mode in Discord (User Settings → Advanced)
2. Right-click your admin role → Copy ID
3. Add to `.env` as `ADMIN_ROLE_ID`

### PPOA Configuration

- `PPOA_REGISTRATION_CODE`: Your apartment's registration code (e.g., "MAVP")
- `DEFAULT_APARTMENT`: Default apartment number for pre-filling forms

## Troubleshooting

### Bot won't start

- **Check `.env` file**: Ensure `DISCORD_BOT_TOKEN` is set
- **Check database**: Run `docker-compose logs postgres`
- **Check migrations**: Run `docker-compose up flyway`

### Playwright errors

- **Missing browsers**: Run `playwright install chromium`
- **Headless issues**: Set `ENVIRONMENT=development` for debugging

### Database connection errors

- **Wrong credentials**: Verify `.env` matches docker-compose settings
- **Port conflict**: Change `POSTGRES_PORT` in `.env`

### Commands not appearing

- **Not synced**: Bot syncs commands on startup, wait ~1 minute
- **Permissions**: Ensure bot has `applications.commands` scope

## Security Notes

- ✅ Never commit `.env` file to git
- ✅ Use strong database passwords
- ✅ Restrict admin commands to trusted roles
- ✅ Keep Discord bot token secret
- ✅ Review Playwright automation logs periodically

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Acknowledgments

- Built for apartment communities using Parking Permits of America
- Inspired by the need to simplify repetitive parking registration
