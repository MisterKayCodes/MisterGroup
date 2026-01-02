# Telegram Conversation Simulator - ChatGPT Prompt

Use this prompt to generate properly formatted JSON conversation files for the Telegram Conversation Simulator Bot.

---

## Prompt for ChatGPT

```
I need you to create a conversation JSON file for my Telegram group simulation bot. The bot uses multiple user sessions to simulate realistic group chats with time-based scheduling.

**AVAILABLE SENDERS (use these exact names):**
- AmySaunders
- EduardaSilva
- janrunge
- Jorge
- JuanMccoy
- Julia
- LenaCrowde
- NawarAhmad
- NermeenAhmad
- NicoleMitchell
- ShannonMiranda

---

## JSON FORMATS

There are TWO formats you can use:

### FORMAT 1: IMMEDIATE MODE (Simple)
Messages run immediately when simulation starts:

{
  "name": "Conversation Title",
  "description": "Brief description",
  "mode": "immediate",
  "messages": [
    {
      "sender_name": "Julia",
      "message_type": "text",
      "content": "Hello everyone!",
      "delay_before": 2.0
    }
  ]
}

### FORMAT 2: SCHEDULED MODE (Time-Based)
Messages run automatically at specific times with different participant groups:

{
  "name": "Daily Group Chat",
  "description": "Full day simulation with different activity periods",
  "mode": "scheduled",
  "schedule": [
    {
      "time": "08:00",
      "label": "Morning Crew",
      "participants": ["Julia", "Jorge", "AmySaunders"],
      "repeat": "weekdays",
      "enabled": true,
      "messages": [
        {"sender_name": "Julia", "content": "Good morning team!", "delay_before": 1.0},
        {"sender_name": "Jorge", "content": "Morning! Ready for the day?", "delay_before": 2.5}
      ]
    },
    {
      "time": "14:00",
      "label": "Afternoon Discussion",
      "participants": ["NawarAhmad", "EduardaSilva", "LenaCrowde", "NicoleMitchell"],
      "repeat": "daily",
      "enabled": true,
      "messages": [...]
    },
    {
      "time": "20:00",
      "label": "Evening - Everyone Active",
      "participants": "all",
      "repeat": "daily",
      "enabled": true,
      "messages": [...]
    }
  ]
}

---

## FIELD REFERENCE

### Message Fields:
| Field | Required | Description |
|-------|----------|-------------|
| sender_name | Yes | Must match one of the available senders exactly (case-sensitive) |
| message_type | No | "text" (default), "photo", "video", "voice", "document", "sticker" |
| content | Yes | The actual message text |
| delay_before | No | Seconds to wait before sending (default: 1.0) |
| typing_duration | No | Custom typing time in seconds (auto-calculated if not set) |
| media_url | No | URL or path to media file (required for non-text types) |

### Scheduled Period Fields:
| Field | Required | Description |
|-------|----------|-------------|
| time | Yes | Time in 24-hour format "HH:MM" (e.g., "08:00", "14:30", "20:00") |
| label | Yes | Name for this period (e.g., "Morning Chat", "Lunch Break") |
| participants | Yes | List of sender names OR "all" for everyone |
| messages | Yes | Array of messages for this period |
| repeat | No | "daily" (default), "weekdays", "weekends", or "once" |
| enabled | No | true (default) or false to disable this period |

---

## TIPS FOR REALISTIC CONVERSATIONS

1. **Natural Timing:**
   - Use delay_before between 1.0-8.0 seconds
   - Short delays (1-2s) for quick replies
   - Longer delays (4-8s) for thoughtful responses

2. **Group Dynamics:**
   - Have 3-5 different senders per period
   - Include reactions, questions, and acknowledgments
   - Mix short and medium-length messages

3. **Time Period Design:**
   - Morning (7-9 AM): Greetings, daily planning
   - Midday (12-2 PM): Casual chat, lunch discussions
   - Afternoon (3-5 PM): Work updates, questions
   - Evening (7-9 PM): Wrap-up, social chat

4. **Participant Groups:**
   - Use different people at different times
   - "all" for peak activity periods
   - Smaller groups for focused discussions

---

## COMPLETE EXAMPLE - SCHEDULED MODE

{
  "name": "Tech Startup Daily Chat",
  "description": "Simulated daily group conversation for a tech startup team",
  "mode": "scheduled",
  "schedule": [
    {
      "time": "08:30",
      "label": "Morning Standup",
      "participants": ["Julia", "Jorge", "AmySaunders", "janrunge"],
      "repeat": "weekdays",
      "enabled": true,
      "messages": [
        {"sender_name": "Julia", "content": "Good morning everyone! Ready for standup?", "delay_before": 1.0},
        {"sender_name": "Jorge", "content": "Morning! Yes, let me grab my coffee first ☕", "delay_before": 3.0},
        {"sender_name": "AmySaunders", "content": "Hey team! I'm here", "delay_before": 2.0},
        {"sender_name": "janrunge", "content": "Present! Working on the API integration today", "delay_before": 2.5},
        {"sender_name": "Julia", "content": "Great! Jorge, what's your focus today?", "delay_before": 1.5},
        {"sender_name": "Jorge", "content": "Finishing up the dashboard components. Should be done by EOD", "delay_before": 4.0},
        {"sender_name": "AmySaunders", "content": "Nice! I'll be reviewing PRs and working on docs", "delay_before": 2.0},
        {"sender_name": "Julia", "content": "Perfect. Let's sync again at 4pm. Good luck everyone! 💪", "delay_before": 2.0}
      ]
    },
    {
      "time": "12:30",
      "label": "Lunch Break Chat",
      "participants": ["NawarAhmad", "EduardaSilva", "LenaCrowde"],
      "repeat": "daily",
      "enabled": true,
      "messages": [
        {"sender_name": "NawarAhmad", "content": "Anyone else taking lunch now?", "delay_before": 1.0},
        {"sender_name": "EduardaSilva", "content": "Yeah! Just heating up leftovers", "delay_before": 2.5},
        {"sender_name": "LenaCrowde", "content": "Same here. What did everyone bring today?", "delay_before": 2.0},
        {"sender_name": "NawarAhmad", "content": "Got some pasta from last night. It's actually better today 😄", "delay_before": 3.0},
        {"sender_name": "EduardaSilva", "content": "Haha leftovers are the best sometimes", "delay_before": 2.0}
      ]
    },
    {
      "time": "16:00",
      "label": "Afternoon Sync",
      "participants": ["Julia", "Jorge", "AmySaunders", "janrunge", "NicoleMitchell"],
      "repeat": "weekdays",
      "enabled": true,
      "messages": [
        {"sender_name": "Julia", "content": "Quick sync everyone - how's progress?", "delay_before": 1.0},
        {"sender_name": "Jorge", "content": "Dashboard is 90% done! Just polishing animations", "delay_before": 3.0},
        {"sender_name": "janrunge", "content": "API integration complete. Running tests now", "delay_before": 2.5},
        {"sender_name": "NicoleMitchell", "content": "I reviewed 3 PRs, approved 2. One needs minor fixes", "delay_before": 2.0},
        {"sender_name": "AmySaunders", "content": "Docs are updated for the new features", "delay_before": 2.0},
        {"sender_name": "Julia", "content": "Excellent work team! 🎉", "delay_before": 1.5}
      ]
    },
    {
      "time": "20:00",
      "label": "Evening Social",
      "participants": "all",
      "repeat": "daily",
      "enabled": true,
      "messages": [
        {"sender_name": "ShannonMiranda", "content": "Anyone watching the game tonight?", "delay_before": 1.0},
        {"sender_name": "JuanMccoy", "content": "Which game?", "delay_before": 2.0},
        {"sender_name": "ShannonMiranda", "content": "The championship finals!", "delay_before": 1.5},
        {"sender_name": "NermeenAhmad", "content": "Oh yes! I've been waiting all week", "delay_before": 2.5},
        {"sender_name": "Jorge", "content": "Count me in. Predicting a close one 🏆", "delay_before": 3.0},
        {"sender_name": "Julia", "content": "Have fun everyone! I'll catch the highlights tomorrow", "delay_before": 2.0},
        {"sender_name": "AmySaunders", "content": "Same here. Enjoy the game! 🎉", "delay_before": 2.0}
      ]
    }
  ]
}

---

## COMPLETE EXAMPLE - IMMEDIATE MODE

{
  "name": "Quick Team Discussion",
  "description": "A simple conversation that runs immediately",
  "mode": "immediate",
  "messages": [
    {"sender_name": "Julia", "message_type": "text", "content": "Hey everyone, quick question about the project", "delay_before": 1.0},
    {"sender_name": "Jorge", "message_type": "text", "content": "Sure, what's up?", "delay_before": 2.5},
    {"sender_name": "AmySaunders", "message_type": "text", "content": "I'm listening", "delay_before": 1.5},
    {"sender_name": "Julia", "message_type": "text", "content": "Should we use the new framework or stick with the current one?", "delay_before": 3.0},
    {"sender_name": "janrunge", "message_type": "text", "content": "I'd say stick with current for now. Less risk", "delay_before": 4.0},
    {"sender_name": "Jorge", "message_type": "text", "content": "Agreed. We can evaluate the new one for v2", "delay_before": 2.5},
    {"sender_name": "Julia", "message_type": "text", "content": "Makes sense. Thanks team! 👍", "delay_before": 2.0}
  ]
}

---

Now create a conversation about: [YOUR TOPIC HERE]

Specify if you want IMMEDIATE mode (runs when you start it) or SCHEDULED mode (runs automatically at specific times).
```

---

## Bot Commands Reference

| Command | Description |
|---------|-------------|
| `/upload_json` | Upload a conversation JSON file |
| `/show_preview` | Preview the loaded conversation |
| `/start_simulation` | Start immediate mode simulation |
| `/stop_simulation` | Stop current simulation |
| `/pause_simulation` | Pause simulation |
| `/resume_simulation` | Resume paused simulation |
| `/schedule_status` | View scheduled periods and status |
| `/start_scheduler` | Start automatic scheduled execution |
| `/stop_scheduler` | Stop the scheduler |
| `/run_period <label>` | Manually run a specific period |
| `/set_group <id>` | Set target group for messages |
| `/set_typing_speed <fast\|normal\|slow>` | Adjust typing speed |

---


For example:

“Create a scheduled JSON conversation about crypto market updates, 120 messages, broken into morning, afternoon, evening periods.”

or

“Create an immediate JSON conversation, 40 messages, about the group discussing the bot’s profits.”


Made by Mister 💛
