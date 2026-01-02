# Telegram Conversation Simulator Bot - User Guide

## Quick Start

1. Start a chat with your bot on Telegram
2. Send `/start` to see the main menu
3. Use the keyboard buttons or commands to navigate

## Main Features

### Sessions Management
Sessions are Telegram user accounts that will send messages in your target group.

- **Add Session**: Add a new Telegram session using a session string
- **View Sessions**: See all connected sessions
- **Remove Session**: Delete a session from the bot

### Conversation Setup

#### Text Format (Easy Method)
You can write conversations in a simple text format:
```
Alice: Hello everyone!
Bob: Hey Alice, how are you?
Alice: I'm great, thanks for asking!
```

Then use **Convert Text** to turn this into the proper JSON format.

#### JSON Format (Advanced)
For more control, upload a JSON file with this structure:
```json
{
  "messages": [
    {
      "sender_name": "Alice",
      "content": "Hello everyone!",
      "message_type": "text",
      "delay_before": 5
    },
    {
      "sender_name": "Bob",
      "content": "Hey Alice!",
      "message_type": "text",
      "delay_before": 8
    }
  ]
}
```

#### Message Types
- `text` - Regular text message
- `photo` - Photo with optional caption
- `video` - Video with optional caption
- `voice` - Voice note
- `document` - File/document

### Media Tags (Advanced)
Add media to messages using category tags:
```
Alice: Check out this result! [BALANCE]
```

The `[BALANCE]` tag will be replaced with media from the BALANCE category.

**Important:** Media is sourced from Telegram channels, not external URLs. The bot fetches media directly from your source channels using Telethon.

#### How Media Works
1. You have a Telegram channel with images/videos (e.g., `t.me/yourchannel`)
2. The bot scans the channel and indexes all media messages by their message IDs
3. Categories map to index ranges (e.g., BALANCE uses messages 1-20)
4. During simulation, the bot fetches media from the source channel and sends it to the target group

#### Setting Up Media Categories
1. Press **Media Setup** button
2. **Add Channel**: Enter your source channel ID or username (e.g., `-1001234567890` or `@yourchannel`)
3. **Scan Channel**: The bot indexes all media in the channel with message IDs
4. **Create Category**: Set a name (e.g., BALANCE) and index range (e.g., 0-20)
5. Use `[CATEGORY_NAME]` tags in your conversation scripts

### Target Group
Set the Telegram group where messages will be sent:
1. Add your bot and session accounts to the target group
2. Get the group ID (forward a message from the group to @userinfobot)
3. Use `/set_group <group_id>` to set it

### Running Simulations

#### Immediate Mode
For conversations without schedules:
1. Upload your conversation (text or JSON)
2. Set your target group
3. Press **Start Simulation** or use `/start_simulation`

Controls during simulation:
- **Pause**: Temporarily stop the simulation
- **Resume**: Continue from where you paused
- **Stop**: End the simulation completely

#### Scheduled Mode
For time-based conversations, include a `schedule` in your JSON:
```json
{
  "schedule": [
    {
      "label": "Morning",
      "time": "09:00",
      "repeat": "daily",
      "enabled": true,
      "participants": "all",
      "messages": [...]
    }
  ]
}
```

Repeat options: `daily`, `weekdays`, `weekends`, `once`

Use `/start_scheduler` to enable automatic scheduling.

### Typing Speed
Control how fast messages appear to be typed:
- **Fast**: 3-9 second delays
- **Normal**: 10-26 second delays (default)
- **Slow**: 27-50 second delays

## Commands Reference

| Command | Description |
|---------|-------------|
| `/start` | Show main menu |
| `/help` | Show help message |
| `/status` | Check bot and simulation status |
| `/sessions` | List all sessions |
| `/add_session` | Add a new session |
| `/upload_json` | Upload conversation JSON |
| `/set_group <id>` | Set target group |
| `/start_simulation` | Start immediate simulation |
| `/stop_simulation` | Stop running simulation |
| `/start_scheduler` | Start automatic scheduler |
| `/stop_scheduler` | Stop scheduler |
| `/media_setup` | Open media configuration |

## Tips

1. **Test First**: Use a test group before running in your main group
2. **Session Strings**: Generate session strings using Telethon's StringSession
3. **Timing**: Use realistic delays for natural-looking conversations
4. **Media**: Scan channels with varied content for better media variety
5. **Logs**: Check the logs folder for debugging if issues occur

## Media Source Channels

Media in this bot comes from Telegram channels, not local files. Here's how it works:

### Example Setup
1. Create a private Telegram channel for your media (e.g., "My Media Library")
2. Upload all your images/videos to this channel
3. Note the channel ID (forward a message to @userinfobot)
4. In the bot, use **Media Setup** > **Add Channel** with your channel ID
5. **Scan** the channel to index all media
6. Create categories like:
   - `BALANCE`: Messages 1-20 (balance screenshots)
   - `PROFIT`: Messages 21-40 (profit images)
   - `LIFESTYLE`: Messages 41-60 (lifestyle photos)

### Using Media in Conversations
```
Alice: Just checked my balance [BALANCE]
Bob: Nice! Here's my profit today [PROFIT]
Alice: Living the dream [LIFESTYLE]
```

The bot will:
1. Detect the `[BALANCE]` tag
2. Fetch the next media from your source channel (using message ID)
3. Send it to the target group with "Just checked my balance" as caption
4. Automatically rotate through the category's media range

## Troubleshooting

- **Session errors**: Make sure API_ID and API_HASH are set correctly
- **Group not found**: Verify the group ID and that sessions are members
- **Messages not sending**: Check that sessions are connected and not restricted
- **Media not appearing**: 
  - Ensure the source channel is added and scanned
  - Verify categories are created with correct index ranges
  - Check that sessions have access to the source channel
  - Make sure the message IDs in the range actually contain media
- **Media fetch failed**: The session account must be a member of the source channel to fetch media
- **Tag not recognized**: Category names are case-sensitive (use `[BALANCE]` not `[balance]`)
