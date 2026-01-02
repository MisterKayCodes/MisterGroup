# Telegram Conversation Simulator Bot - Complete Guide
**Made by Mister 💛**

This is the ultimate guide for the Telegram Conversation Simulator Bot. It covers everything from basic setup to advanced features, including how to use ChatGPT to generate conversations in the correct format.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Concepts](#core-concepts)
3. [Session Management](#session-management)
4. [Conversation Formats](#conversation-formats)
   - [Text Format (Easy Method)](#text-format-easy-method)
   - [JSON Format (Advanced)](#json-format-advanced)
   - [TXT File Upload with Batches](#txt-file-upload-with-batches)
5. [Scheduling Conversations](#scheduling-conversations)
6. [Media Setup](#media-setup)
   - [How Media Tags Work](#how-media-tags-work)
   - [Setting Up Media Channels](#setting-up-media-channels)
   - [Creating Categories](#creating-categories)
   - [Quick Category Templates](#quick-category-templates)
7. [Running Simulations](#running-simulations)
8. [ChatGPT Prompts](#chatgpt-prompts)
   - [Prompt for Immediate Mode](#prompt-for-immediate-mode)
   - [Prompt for Scheduled Mode](#prompt-for-scheduled-mode)
   - [Prompt for TXT Batch Format](#prompt-for-txt-batch-format)
   - [Prompt for Media Tags](#prompt-for-media-tags)
9. [Command Reference](#command-reference)
10. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Step 1: Set Up Environment Variables

Create a `.env` file with your Telegram credentials:

```bash
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_ID=your_telegram_user_id
API_ID=your_api_id_from_my_telegram_org
API_HASH=your_api_hash_from_my_telegram_org
LOG_LEVEL=INFO
```

**Where to get credentials:**
- `BOT_TOKEN`: Talk to [@BotFather](https://t.me/botfather) on Telegram
- `ADMIN_ID`: Your Telegram user ID (find using [@userinfobot](https://t.me/userinfobot))
- `API_ID` & `API_HASH`: Get from [my.telegram.org](https://my.telegram.org)

### Step 2: Install & Run

```bash
pip install -r requirements.txt
python main.py
```

### Step 3: Start Using the Bot

1. Open Telegram and find your bot
2. Send `/start` to see the main menu
3. Use the keyboard buttons to navigate

---

## Core Concepts

### What This Bot Does

This bot simulates realistic group conversations by:
1. Using multiple Telegram user accounts (sessions) to send messages
2. Adding realistic typing delays between messages
3. Supporting scheduled message delivery at specific times
4. Including media (photos/videos) from your channels

### Key Terms

| Term | Meaning |
|------|---------|
| **Session** | A Telegram user account that sends messages in the simulation |
| **Conversation** | A script of messages to be simulated |
| **Batch** | A group of messages scheduled for a specific time |
| **Category** | A named group of media items (e.g., BALANCE, DEPOSIT) |
| **Media Tag** | A placeholder like `[BALANCE]` that gets replaced with an image |

---

## Session Management

Sessions are Telegram user accounts that will send messages in your target group.

### Adding Sessions

1. Press **👥 Sessions** button
2. Click **➕ Add Session**
3. Send the session string (generated using Telethon's StringSession)

### Session String Format

A session string looks like this:
```
1BQANOTEuMDguMjIyLjIyMgG7...
```

You can generate session strings using Telethon scripts or online generators.

### Important Notes

- Session names in your conversation MUST match registered session names exactly
- Sessions must be members of the target group to send messages
- Use `/test_session <name>` to verify a session works

---

## Conversation Formats

The bot supports multiple ways to create conversations:

### Text Format (Easy Method)

The simplest way to create a conversation. Just type messages in this format:

```
Alice: Hello everyone!
Bob: Hey Alice, how are you?
Alice: I'm great, thanks for asking!
Charlie: What's everyone up to today?
```

**How to use:**
1. Press **🗂️ Upload JSON** button
2. Click **📝 Convert Text to JSON**
3. Select delay speed (Fast/Normal/Slow)
4. Choose Instant or Scheduled mode
5. Paste your text

### JSON Format (Advanced)

For more control, use JSON structure:

#### Immediate Mode JSON

```json
{
  "name": "My Conversation",
  "description": "A simple chat",
  "mode": "immediate",
  "messages": [
    {
      "sender_name": "Alice",
      "message_type": "text",
      "content": "Hello everyone!",
      "delay_before": 2.0
    },
    {
      "sender_name": "Bob",
      "message_type": "text", 
      "content": "Hey Alice!",
      "delay_before": 3.0
    }
  ]
}
```

#### Scheduled Mode JSON

```json
{
  "name": "Daily Group Chat",
  "description": "Scheduled conversation",
  "mode": "scheduled",
  "schedule": [
    {
      "time": "09:00",
      "label": "Morning Chat",
      "participants": ["Alice", "Bob", "Charlie"],
      "repeat": "daily",
      "enabled": true,
      "messages": [
        {"sender_name": "Alice", "content": "Good morning!", "delay_before": 1.0},
        {"sender_name": "Bob", "content": "Morning everyone!", "delay_before": 2.5}
      ]
    },
    {
      "time": "18:00",
      "label": "Evening Discussion",
      "participants": "all",
      "repeat": "weekdays",
      "enabled": true,
      "messages": [
        {"sender_name": "Charlie", "content": "How was everyone's day?", "delay_before": 1.0}
      ]
    }
  ]
}
```

### TXT File Upload with Batches

Upload a `.txt` file with multiple batches separated by markers:

```
---BATCH: Morning Chat | 09:00 | daily---
Alice: Good morning team!
Bob: Hey everyone, ready for the day?
Charlie: Coffee first, then work!

---BATCH: Lunch Break | 12:30 | weekdays---
Alice: Anyone else starving?
Bob: Yeah, what's for lunch today?
Charlie: I brought leftovers

---BATCH: Evening Wrap-up | 18:00 | daily---
Alice: Great work today everyone!
Bob: See you all tomorrow
Charlie: Have a good evening!
```

**Batch Header Format:**
```
---BATCH: [Name] | [Time HH:MM] | [Repeat Pattern]---
```

**Repeat Patterns:**
- `daily` - Every day
- `weekdays` - Monday to Friday
- `weekends` - Saturday and Sunday
- `once` - Run once only

---

## Scheduling Conversations

### Repeat Patterns

| Pattern | When It Runs |
|---------|--------------|
| `daily` | Every day at the specified time |
| `weekdays` | Monday through Friday |
| `weekends` | Saturday and Sunday |
| `once` | Only once, then disabled |

### All Times Are in UTC

⚠️ **Important:** All scheduled times use UTC timezone!

To convert your local time:
- US Eastern (EST): Add 5 hours (or 4 during daylight saving)
- US Pacific (PST): Add 8 hours (or 7 during daylight saving)
- UK (GMT): Same as UTC (add 1 during BST)
- Central Europe (CET): Subtract 1 hour (or 2 during CEST)

### Viewing Schedule Status

Press **⏰ Schedule** button → **📊 Schedule Status** to see:
- All scheduled batches
- Next execution times
- Countdown to upcoming posts

---

## Media Setup

Media tags let you include images and videos from your Telegram channels in conversations.

### How Media Tags Work

1. You have a Telegram channel with images/videos
2. The bot scans and indexes all media in that channel
3. You create **categories** that map to specific media ranges
4. In your conversation, use `[CATEGORY_NAME]` tags
5. During simulation, the bot replaces tags with actual media

**Example conversation with media tags:**
```
Alice: Just checked my balance [BALANCE]
Bob: Nice! Here's my deposit confirmation [DEPOSIT]
Charlie: Living the dream [LIFESTYLE]
```

### Setting Up Media Channels

1. Press **🎬 Media Setup** button
2. Click **📡 Add New Media Channel**
3. Enter your channel:
   - Username: `@yourchannel`
   - ID: `-1001234567890`
   - Link: `https://t.me/yourchannel`
4. Wait for the bot to scan all media

### Creating Categories

After adding a channel:

1. Click **📁 Manage Categories**
2. Select your channel
3. Define categories with index ranges:

```
BALANCE: 0-20
DEPOSIT: 21-40
WITHDRAW: 41-60
PROFIT: 61-80
LIFESTYLE: 81-100
```

**Format:** `CATEGORY_NAME: start-end`

You can also use multiple ranges:
```
MIXED: 0-10, 50-60, 90-100
```

### Quick Category Templates

The bot offers pre-made templates for common categories:

| Template | Suggested Use |
|----------|---------------|
| **BALANCE** | Account balance screenshots |
| **DEPOSIT** | Deposit confirmation images |
| **PROFIT** | Profit/earnings screenshots |
| **LIFESTYLE** | Lifestyle photos |
| **WITHDRAW** | Withdrawal confirmations |

### How Media Rotation Works

The bot uses a **circular queue** for each category:
1. First message with `[BALANCE]` uses media index 0
2. Second message with `[BALANCE]` uses media index 1
3. When it reaches the end, it wraps back to the beginning

This ensures variety in your simulated conversations.

---

## Running Simulations

### Immediate Mode

For conversations that run right away:

1. Upload your conversation (text or JSON)
2. Set target group with **⚙️ Settings** → **🎯 Set Target Group**
3. Press **▶️ Start Sim**

### Scheduled Mode

For time-based conversations:

1. Upload scheduled conversation or TXT with batches
2. Set target group
3. Press **⏰ Schedule** → **▶️ Start Scheduler**

### Controls During Simulation

- **⏸️ Pause** - Temporarily stop
- **▶️ Resume** - Continue from where you paused
- **⏹️ Stop** - End completely

---

## ChatGPT Prompts

Use these prompts to generate properly formatted conversations with ChatGPT.

### Prompt for Immediate Mode

```
I need you to create a conversation for my Telegram bot simulation. Output ONLY the text in this exact format (one message per line):

SenderName: Message content here

Rules:
1. Use these exact sender names: Alice, Bob, Charlie, David, Emma
2. Each line must be: Name: Message (with a colon after the name)
3. Create 20 messages total
4. Make the conversation natural and flowing
5. Topic: [YOUR TOPIC HERE]

Do not include any JSON, just the plain text format.
```

### Prompt for Scheduled Mode

```
Create a JSON conversation file for my Telegram simulation bot with scheduled time periods.

Use these exact sender names: Alice, Bob, Charlie, David, Emma

Create a JSON with this structure:
{
  "name": "[Conversation Title]",
  "mode": "scheduled",
  "schedule": [
    {
      "time": "09:00",
      "label": "Morning Discussion",
      "participants": ["Alice", "Bob", "Charlie"],
      "repeat": "daily",
      "enabled": true,
      "messages": [
        {"sender_name": "Alice", "content": "message here", "delay_before": 2.0}
      ]
    }
  ]
}

Requirements:
1. Create 4 time periods: 09:00, 12:00, 15:00, 20:00
2. Each period should have 10-15 messages
3. Use different participant groups for each period
4. Topic: [YOUR TOPIC HERE]
5. delay_before should be between 1.0 and 5.0 seconds
6. Output valid JSON only
```

### Prompt for TXT Batch Format

```
Create a TXT file for my Telegram bot with multiple scheduled batches.

Use these sender names: Alice, Bob, Charlie, David, Emma

Format each batch like this:
---BATCH: [Batch Name] | [Time in HH:MM] | [daily/weekdays/weekends/once]---
SenderName: Message content
SenderName: Another message

Requirements:
1. Create 5 batches throughout the day (08:00, 11:00, 14:00, 17:00, 21:00)
2. Each batch should have 8-12 messages
3. Use "daily" for most batches
4. Topic: [YOUR TOPIC HERE]

Example output:
---BATCH: Morning Greetings | 08:00 | daily---
Alice: Good morning everyone!
Bob: Hey Alice, ready for today?
```

### Prompt for Media Tags

```
Create a conversation with media tags for my Telegram simulation bot.

Available media categories (use these exact names in brackets):
- [BALANCE] - for balance screenshots
- [DEPOSIT] - for deposit confirmations
- [PROFIT] - for profit images
- [LIFESTYLE] - for lifestyle photos
- [WITHDRAW] - for withdrawal confirmations

Format:
SenderName: Message with optional [CATEGORY] tag

Rules:
1. Use sender names: Alice, Bob, Charlie, David, Emma
2. Include media tags naturally in messages
3. Not every message needs a media tag
4. Create 25 messages total
5. Topic: [YOUR TOPIC - e.g., crypto trading group discussion]

Example:
Alice: Just checked my account [BALANCE]
Bob: Wow nice! I got a deposit this morning [DEPOSIT]
Charlie: That's what I like to see
Alice: Here's my profit from yesterday [PROFIT]
```

### Prompt for Month-Long Schedule

```
Create a TXT file with scheduled conversations for an entire month of simulation.

Use sender names: Alice, Bob, Charlie, David, Emma, Frank, Grace

Create batches for EACH DAY of the month following this pattern:

For weekdays (Monday-Friday):
- 09:00 | weekdays - Morning standup (5-8 messages)
- 12:30 | weekdays - Lunch chat (4-6 messages)
- 17:00 | weekdays - End of day (4-6 messages)

For weekends (Saturday-Sunday):
- 11:00 | weekends - Casual weekend chat (6-10 messages)
- 19:00 | weekends - Evening social (6-10 messages)

Format:
---BATCH: [Name] | [Time] | [repeat pattern]---
SenderName: Message

Topic: [YOUR TOPIC - e.g., tech startup team, crypto trading group, etc.]

Make conversations natural with:
- Greetings and sign-offs
- Questions and answers
- Reactions and acknowledgments
- Mix of short and medium messages
```

---

## Command Reference

### Main Commands

| Command | Description |
|---------|-------------|
| `/start` | Show main menu |
| `/help` | Show help message |
| `/status` | Check bot status |

### Session Commands

| Command | Description |
|---------|-------------|
| `/add_session` | Add a new session |
| `/list_sessions` | View all sessions |
| `/remove_session <name>` | Remove a session |
| `/test_session <name>` | Test session connectivity |

### Conversation Commands

| Command | Description |
|---------|-------------|
| `/upload_json` | Upload conversation (reply to file) |
| `/upload_txt` | Upload TXT file with batches |
| `/show_preview` | Preview loaded conversation |
| `/start_simulation` | Start immediate simulation |
| `/stop_simulation` | Stop simulation |
| `/pause_simulation` | Pause simulation |
| `/resume_simulation` | Resume simulation |

### Schedule Commands

| Command | Description |
|---------|-------------|
| `/schedule_status` | View scheduled periods |
| `/start_scheduler` | Start automatic scheduling |
| `/stop_scheduler` | Stop scheduler |
| `/run_period <label>` | Manually run a specific period |

### Queue Commands

| Command | Description |
|---------|-------------|
| `/queue_status` | View queued conversations |
| `/clear_queue` | Clear all queued conversations |
| `/process_queue` | Manually process next queued item |

**How the Queue Works:**
- When you try to start an immediate simulation while the scheduler is running, the conversation is automatically queued
- Queued conversations run automatically after all scheduled posts complete
- You can view, clear, or manually process the queue at any time

### Settings Commands

| Command | Description |
|---------|-------------|
| `/set_group <id>` | Set target group |
| `/set_typing_speed <fast\|normal\|slow>` | Adjust typing speed |

### Media Commands

| Command | Description |
|---------|-------------|
| `/media_setup` | Open media configuration |
| `/media_help` | Show media setup guide |

---

## Troubleshooting

### Bot doesn't respond
- Check that `BOT_TOKEN` is correct in `.env`
- Verify `ADMIN_ID` matches your Telegram user ID
- Check logs with **📄 Logs** button

### Session errors
- Ensure `API_ID` and `API_HASH` are set correctly
- Telethon sessions must be pre-authorized
- Check session status with `/test_session`

### Messages not sending
- Verify target group is set
- Ensure conversation is uploaded
- Check that session names match participants
- Sessions must be members of the target group

### Media not appearing
- Ensure the source channel is added and scanned
- Verify categories are created with correct index ranges
- Check that sessions have access to the source channel
- Category names are case-sensitive: use `[BALANCE]` not `[balance]`

### Scheduled posts not running
- Make sure scheduler is started with **▶️ Start Scheduler**
- All times are in UTC - check your conversion
- Verify the period is enabled in schedule status

### "Missing sessions" warning
- The participant names in your conversation don't match any registered sessions
- Add the missing sessions or update your conversation to use existing session names

---

## Message Field Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `sender_name` | string | Must match a registered session name exactly |
| `content` | string | The message text |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `message_type` | string | "text" | "text", "photo", "video", "voice", "document" |
| `delay_before` | float | 1.0 | Seconds to wait before sending |
| `typing_duration` | float | auto | Custom typing duration |
| `media_url` | string | null | Path/URL to media (for non-text types) |

### Schedule Period Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `time` | string | required | Time in "HH:MM" format (24-hour, UTC) |
| `label` | string | required | Name for this period |
| `participants` | array/string | required | List of names or "all" |
| `messages` | array | required | Array of messages |
| `repeat` | string | "daily" | "daily", "weekdays", "weekends", "once" |
| `enabled` | boolean | true | Whether this period is active |

---

## Delay Speed Reference

| Speed | Delay Range | Typing Duration | Best For |
|-------|-------------|-----------------|----------|
| 🐇 Fast | 3-9 seconds | 1.5-6.3 seconds | Active chats, quick discussions |
| 🐢 Normal | 10-26 seconds | 5-18 seconds | Natural conversations |
| 🐌 Slow | 27-50 seconds | 13.5-35 seconds | Thoughtful discussions |

---

## Tips & Best Practices

1. **Test First**: Use a test group before running in your main group
2. **Match Names**: Ensure session names match conversation participant names exactly
3. **Use Realistic Delays**: Normal speed (10-26s) feels most natural
4. **Media Variety**: Upload many images to your media channel for variety
5. **Check Logs**: Review logs if something isn't working
6. **UTC Time**: Always remember schedule times are in UTC
7. **Preview First**: Always preview before starting a simulation
8. **Backup Sessions**: Keep a backup of your session strings

---

## Security Notes

⚠️ **Important:**
- Never share your `.env` file or expose your tokens
- Keep session strings secure - they provide full account access
- Only add trusted sessions to the bot
- The bot is admin-only by design for security

---

**Made with 💛 by Mister**
