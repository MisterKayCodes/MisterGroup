# Telegram Conversation Simulator Bot
**Made by Mister 💛**

A powerful Telegram bot that simulates realistic conversations in groups using multiple Telethon sessions. Perfect for testing, demonstrations, or creating engaging conversation scenarios.

## Features

✨ **Key Features:**
- 🤖 Admin-only access for secure operation
- 👥 Multiple Telethon session management
- 🗂️ JSON-based conversation data
- ⚡ Realistic typing simulation with adjustable speeds
- 📝 Comprehensive logging with Loguru
- 🎯 Message type support (text, photo, video, voice, documents)
- ⏸️ Pause/resume simulation controls
- 📊 Real-time statistics and status monitoring

## Technologies

- **aiogram v3** - Modern Telegram Bot framework
- **Telethon** - Telegram client for session management
- **Pydantic** - Data validation and settings management
- **Loguru** - Beautiful and powerful logging
- **JSON** - Simple file-based database

## Installation

### Prerequisites
- Python 3.11+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Telegram API credentials (from [my.telegram.org](https://my.telegram.org))

### Setup Steps

1. **Clone or download this project**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
```bash
cp .env.example .env
```

Edit `.env` file with your credentials:
```env
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_ID=your_telegram_user_id
API_ID=your_api_id_from_my_telegram_org
API_HASH=your_api_hash_from_my_telegram_org
LOG_LEVEL=INFO

# Media Simulation Settings (optional)
MEDIA_MAX_RETRIES=2
MEDIA_RETRY_DELAY=1.0
```

4. **Run the bot:**
```bash
python main.py
```

## Usage Guide

### Getting Started

1. **Start the bot:** Send `/start` to see all available commands
2. **Add Telethon sessions:** Use `/add_session` to register user sessions
3. **Upload conversation:** Use `/upload_json` with a JSON file
4. **Set target group:** Use `/set_group <group_id>` to specify where to simulate
5. **Start simulation:** Use `/start_simulation` to begin!

### Command Reference

#### 📋 General Management
- `/start` - Show command list
- `/help` - Detailed help and instructions
- `/status` - Current bot status and statistics

#### 👥 Session Management
- `/add_session` - Register a new Telethon session
- `/list_sessions` - View all registered sessions
- `/remove_session <name>` - Remove a session
- `/test_session <name>` - Test session connectivity
- `/pause_account <name>` - Pause a specific session
- `/resume_account <name>` - Resume a paused session
- `/pause_all` - Pause all sessions
- `/resume_all` - Resume all sessions

#### 🗂️ Conversation Simulation
- `/upload_json` - Upload conversation data (reply to JSON file)
- `/show_preview` - Preview loaded conversation
- `/start_simulation` - Begin message simulation
- `/stop_simulation` - Stop ongoing simulation
- `/pause_simulation` - Pause simulation
- `/resume_simulation` - Resume paused simulation

#### ⚙️ Configuration
- `/set_group <group_id>` - Set target group for simulation
- `/set_typing_speed <fast|normal|slow>` - Adjust typing speed

#### 🛠️ Maintenance
- `/get_logs` - Retrieve recent log files
- `/restart` - Restart the bot

### JSON Conversation Format

Create a JSON file with the following structure:

```json
{
  "name": "Sample Conversation",
  "description": "A demo conversation",
  "messages": [
    {
      "sender_name": "Alice",
      "message_type": "text",
      "content": "Hello everyone!",
      "delay_before": 1.0
    },
    {
      "sender_name": "Bob",
      "message_type": "text",
      "content": "Hey Alice! How are you?",
      "delay_before": 2.0,
      "typing_duration": 3.0
    },
    {
      "sender_name": "Alice",
      "message_type": "photo",
      "content": "Check out this image!",
      "media_url": "/path/to/image.jpg",
      "delay_before": 1.5
    }
  ]
}
```

**Message Types:**
- `text` - Regular text message
- `photo` - Image with optional caption
- `video` - Video with optional caption
- `voice` - Voice note
- `document` - File/document with optional caption

**Fields:**
- `sender_name` - Must match a registered session name
- `message_type` - Type of message (see above)
- `content` - Message text or caption
- `media_url` - Path or URL to media file (required for non-text types)
- `delay_before` - Seconds to wait before sending (default: 1.0)
- `typing_duration` - Custom typing duration (optional, auto-calculated if not provided)

## Project Structure

```
.
├── main.py                 # Bot entry point
├── config.py               # Centralized configuration management
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── data/
│   ├── database.json      # JSON database
│   └── media.db           # SQLite database for media simulation
├── logs/                  # Log files directory
├── sessions/              # Telethon session files
└── src/
    ├── database/          # Database modules
    │   └── media_tables.py
    ├── models/            # Pydantic data models
    │   ├── session.py
    │   ├── conversation.py
    │   └── config.py
    ├── services/          # Core business logic
    │   ├── session_manager.py
    │   └── simulation_engine.py
    ├── handlers/          # Bot command handlers
    │   ├── admin_commands.py
    │   └── media_setup.py
    └── utils/             # Utilities
        ├── logger.py
        ├── database.py
        ├── media_parser.py
        └── media_circular_queue.py
```

## How to Get Your Telegram User ID

1. Send a message to [@userinfobot](https://t.me/userinfobot)
2. Copy the "Id" number it sends back
3. Use this as your `ADMIN_ID` in `.env`

## How to Get Telethon API Credentials

1. Visit [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Click "API Development Tools"
4. Create a new application
5. Copy `api_id` and `api_hash`
6. Add them to your `.env` file

## Troubleshooting

### Bot doesn't respond
- Check that `BOT_TOKEN` is correct in `.env`
- Verify `ADMIN_ID` matches your Telegram user ID
- Check logs in `logs/` directory

### Session issues
- Ensure `API_ID` and `API_HASH` are set correctly
- Telethon sessions must be pre-authorized
- Check session status with `/test_session`

### Simulation not working
- Verify target group is set with `/set_group`
- Ensure conversation JSON is uploaded with `/upload_json`
- Check that session names in JSON match registered sessions
- Review logs for detailed error messages

## Security Notes

⚠️ **Important:**
- Never share your `.env` file or expose your tokens
- Keep session strings secure - they provide full account access
- Only add trusted sessions to the bot
- The bot is admin-only by design for security

## License

This project is created by **Mister 💛** for educational and demonstration purposes.

## Support

For bugs, issues, or questions, please check the logs first (`/get_logs` command) and review the documentation above.

---

**Made with 💛 by Mister**
