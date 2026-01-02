# MisterGroupV2 - Telegram Conversation Simulator Bot

## Overview

This is a Telegram bot that simulates realistic group conversations using multiple Telethon sessions. The bot allows an admin to orchestrate automated conversations with configurable timing, media attachments, and scheduling patterns. It's designed for demonstrations, testing, or creating engaging conversation scenarios in Telegram groups.

**Core Purpose:** Enable a single admin to control multiple Telegram user sessions that participate in scripted or scheduled conversations within a target group, with realistic typing delays and media support.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Framework
- **Primary Framework:** aiogram v3 for the bot's admin interface
- **Client Framework:** Telethon for managing multiple user sessions that send messages
- **Rationale:** aiogram provides a clean async interface for bot commands, while Telethon enables user-based messaging (not bot-based), which creates more realistic group conversations

### Data Storage
- **Conversation Data:** JSON files (`data/database.json`) for sessions, configuration, and conversation scripts
- **Media Data:** SQLite (`data/media.db`) for media channel scanning and category management
- **Rationale:** JSON provides simplicity for configuration and conversation data that's easily editable, while SQLite handles relational media metadata efficiently

### Session Management
- **Implementation:** Telethon StringSessions stored in JSON database
- **Active Clients:** In-memory dictionary mapping session names to TelegramClient instances
- **Authentication:** Sessions are pre-authorized and stored as session strings
- **Rationale:** Session strings allow persistent authentication without storing credentials, enabling the bot to operate multiple user accounts simultaneously

### Admin Access Control
- **Three-Tier Priority:**
  1. `ADMIN_ID` environment variable (highest priority)
  2. Database-persisted admin_id (from first user)
  3. First-user fallback (if both above are None)
- **Thread Safety:** asyncio.Lock prevents race conditions in single-process deployments
- **Rationale:** Flexible admin assignment supports both explicit configuration and automatic initialization for personal use

### Conversation Simulation Engine
- **Message Types:** Text, photo, video, voice, document, sticker
- **Timing Control:** 
  - Configurable delay ranges (Fast: 3-9s, Normal: 10-26s, Slow: 27-50s)
  - Realistic typing duration simulation
  - Pause/resume capability
- **Execution Modes:**
  - **Immediate:** Manual trigger via `/start_simulation`
  - **Scheduled:** Time-based with repeat patterns (daily, weekdays, weekends, once)
- **State Management:** Tracks running status, pause state, current message index
- **Rationale:** Provides realistic conversation pacing that mimics human behavior

### Media Attachment System
- **Channel Scanning:** Uses Telethon to scan source channels and store media file_ids
- **Category System:** Index-based ranges (e.g., BALANCE: 0-20) map media to conversation contexts
- **Circular Queue:** Auto-advancing pointers ensure media rotation within categories
- **Tag Replacement:** Messages with `[CATEGORY_NAME]` tags automatically attach media
- **Backward Compatible:** Works alongside text-only messages without tags
- **Rationale:** Separates media sourcing from conversation scripts, enabling reusable media libraries

### Text-to-JSON Conversion
- **Input:** Plain conversation text format (`Name: Message`)
- **Processing:** Automatic parsing with randomized delays and typing durations
- **Preview:** Shows formatted JSON before saving
- **Rationale:** Simplifies conversation creation by avoiding manual JSON formatting

### Scheduling System
- **UTC-Based Timing:** All schedules use UTC to avoid timezone issues
- **Repeat Patterns:** Daily, weekdays, weekends, or one-time execution
- **Period Tracking:** Prevents duplicate executions within same day
- **Participant Filtering:** Can specify subset of sessions per scheduled period
- **Rationale:** Enables automated conversation flows without manual intervention

### State Management
- **Simulation State:** Tracks whether simulation is running, paused, current message index
- **Session State:** Per-session connection status and activity tracking
- **Scheduler State:** Running status and executed periods tracking
- **Rationale:** Maintains consistent state across async operations and enables graceful pause/resume

### Logging Strategy
- **Framework:** Loguru with structured formatting
- **Outputs:**
  - Console with colors for development
  - Daily rotating logs (7-day retention)
  - Error-only logs (30-day retention)
- **Rationale:** Comprehensive debugging without excessive disk usage

### Keyboard Interface Design
- **Reply Keyboards:** Persistent main menu for quick access to core functions
- **Inline Keyboards:** Context-specific actions that don't clutter chat
- **Hierarchical Navigation:** Clear back buttons and menu structure
- **Rationale:** Provides intuitive navigation without requiring command memorization

### Deployment Model
- **Supported:** Single-process deployments (Replit, VPS, personal servers)
- **Concurrency:** asyncio-based, handles multiple sessions in one event loop
- **Limitations:** Multi-process deployments require explicit `ADMIN_ID` to avoid race conditions
- **Rationale:** Optimized for personal/admin use cases where simplicity outweighs high-availability needs

## External Dependencies

### Telegram APIs
- **Bot API:** Via aiogram for admin command interface
- **Client API:** Via Telethon for user session management
- **Required Credentials:**
  - `BOT_TOKEN` from @BotFather
  - `API_ID` and `API_HASH` from my.telegram.org (optional, for Telethon features)
- **Integration:** Sessions send messages as regular users, not as bot

### Python Libraries
- **aiogram 3.15.0:** Async Telegram Bot API framework
- **Telethon 1.37.0:** MTProto client for user sessions
- **Pydantic 2.9.2:** Data validation and settings management
- **Loguru 0.7.3:** Logging with rotation and formatting
- **python-dotenv 1.0.1:** Environment variable management
- **pytz:** Timezone support for scheduling
- **python-docx:** Document handling for media

### Data Storage
- **JSON Files:** Self-contained, no external database server required
- **SQLite:** Embedded database for media metadata
- **File System:** Media files referenced by Telegram file_ids (not stored locally)

### Configuration Dependencies
- **Environment Variables:**
  - `BOT_TOKEN` (required)
  - `ADMIN_ID` (optional but recommended)
  - `API_ID`, `API_HASH` (optional, enables Telethon features)
- **Data Directory:** `data/` folder for JSON and SQLite files
- **Logs Directory:** `logs/` folder for rotating log files