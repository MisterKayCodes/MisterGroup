# Quick Start Guide
**Made by Mister 💛**

## Get Started in 3 Steps

### Step 1: Set Up Environment Variables

Create a `.env` file with your Telegram credentials:

```bash
# Required
BOT_TOKEN=your_bot_token_from_botfather

# Optional but recommended
ADMIN_ID=your_telegram_user_id

# Optional (only needed for Telethon session features)
API_ID=your_api_id_from_my_telegram_org
API_HASH=your_api_hash_from_my_telegram_org
```

**Where to get credentials:**
- `BOT_TOKEN`: Talk to [@BotFather](https://t.me/botfather) on Telegram
- `ADMIN_ID`: Your Telegram user ID (find using bots like [@userinfobot](https://t.me/userinfobot))
- `API_ID` & `API_HASH`: Get from [my.telegram.org](https://my.telegram.org)

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Run the Bot

```bash
python main.py
```

That's it! Your bot is now running. 🎉

## First Steps

1. **Open Telegram** and find your bot
2. **Send `/start`** to initialize the bot
3. **You're automatically the admin** (first user becomes admin)
4. **See all commands** with `/help`

## Core Features

### Session Management
- `/add_session` - Add Telethon sessions for simulations
- `/list_sessions` - View all sessions
- `/remove_session` - Delete a session

### Conversation Control
- `/upload_conversation` - Upload conversation JSON
- `/preview_conversation` - Preview loaded conversation
- `/start_simulation` - Start playing the conversation
- `/pause_simulation` - Pause playback
- `/resume_simulation` - Resume from where you paused
- `/stop_simulation` - Stop completely

### Configuration
- `/set_speed` - Adjust typing speed (fast/normal/slow)
- `/set_target` - Set which group to send messages to
- `/status` - Check bot status

### Maintenance
- `/get_logs` - Download bot logs
- `/backup` - Backup all data
- `/restore` - Restore from backup

## Example Conversation JSON

Create a file `conversation.json`:

```json
{
  "messages": [
    {
      "session_name": "Alice",
      "text": "Hey everyone! 👋",
      "delay_after": 2
    },
    {
      "session_name": "Bob",
      "text": "Hi Alice! How's it going?",
      "delay_after": 3
    },
    {
      "session_name": "Alice",
      "text": "Great! Just finished the project",
      "delay_after": 1
    }
  ]
}
```

Upload it with `/upload_conversation` and start with `/start_simulation`.

## Need Help?

- **Full documentation:** See `README.md`
- **Bug reports:** Check `BUG_REPORT.md`
- **Deployment:** Read `DEPLOYMENT_NOTES.md`
- **Logs:** Use `/get_logs` command in the bot

## Security Notes

- Only the admin (you) can use the bot
- All data stored locally in `data/database.json`
- Sessions are encrypted with Telethon's StringSession format
- Logs rotate automatically to save space

---

**Made by Mister 💛**
