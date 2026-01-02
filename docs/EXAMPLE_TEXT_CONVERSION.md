# Text-to-JSON Conversion Feature

## Overview
The bot now supports converting plain conversation text directly into JSON format with automatically randomized delays and typing durations! You can create **Instant** conversations or **Scheduled batches** that run at specific times.

## How to Use

1. Click the "🗂️ Upload JSON" button from the main menu
2. Click "📝 Convert Text to JSON"
3. **Step 1** - Select your preferred delay range:
   - 🐇 **Fast (3-9s)**: Quick-paced conversation
   - 🐢 **Normal (10-26s)**: Natural conversation flow
   - 🐌 **Slow (27-50s)**: Slow, thoughtful responses

4. **Step 2** - Choose when to send:
   - ⚡ **Instant** - Run manually when you start simulation
   - 🕐 **Scheduled** - Set specific UTC times for automatic sending

### Instant Mode
Simply enter your conversation text and it saves immediately. Run with `/start_simulation`.

### Scheduled Mode (NEW!)
Create multiple time-based batches:
1. Enter a **batch name** (e.g., "Morning Discussion")
2. Enter the **time in UTC** (format: HH:MM, e.g., `09:00`, `14:30`)
3. Select **repeat pattern**:
   - 📅 Daily - Every day
   - 💼 Weekdays - Monday to Friday
   - 🏖️ Weekends - Saturday and Sunday
   - 1️⃣ Once - Run once then disable
4. Enter your **conversation text**
5. Choose to **add more time slots** or **save all batches**

You can create multiple batches with different times and conversations!

## Example Input

```
AmySaunders: Did you see that Bitcoin just jumped 11% after the Fed restarted their $38B printing program?
KevinMccarthy: Yeah, it's crazy! The dollar's really weakening now after that weak ADP jobs report.
LenaCrowde: The ADP numbers showed a surprise drop of 32,000 private payrolls in November. Not a good sign.
MarkKosarin: Tech stocks are interesting too. Marvell surged on a strong data center forecast.
AmySaunders: I'm diversifying into crypto now. Can't trust fiat anymore.
KevinMccarthy: Smart move. My portfolio is 60% digital assets already.
```

## What Happens

The bot will:
1. Parse each line into a separate message
2. Assign random delays within your selected range (e.g., 10-26s for Normal)
3. Assign random typing durations within the range
4. Create a valid JSON conversation file
5. Save it to the database
6. Show you a preview

## Example Output Structure

```json
{
  "name": "Converted Conversation",
  "description": "Auto-generated from text with normal delay range",
  "mode": "immediate",
  "messages": [
    {
      "sender_name": "AmySaunders",
      "message_type": "text",
      "content": "Did you see that Bitcoin just jumped 11%?",
      "delay_before": 15.23,
      "typing_duration": 8.45
    },
    {
      "sender_name": "KevinMccarthy",
      "message_type": "text",
      "content": "Yeah, it's crazy! The dollar's weakening.",
      "delay_before": 12.67,
      "typing_duration": 6.89
    }
  ]
}
```

## Delay Ranges

### Fast (3-9 seconds)
- Perfect for: Active group chats, quick discussions
- Delay range: 3-9 seconds between messages
- Typing range: 1.5-6.3 seconds

### Normal (10-26 seconds)
- Perfect for: Natural conversations, realistic timing
- Delay range: 10-26 seconds between messages
- Typing range: 5-18.2 seconds

### Slow (27-50 seconds)
- Perfect for: Thoughtful discussions, professional groups
- Delay range: 27-50 seconds between messages
- Typing range: 13.5-35 seconds

## Benefits

✅ **No manual JSON editing** - Just paste your conversation text
✅ **Randomized timing** - Each message gets unique, realistic delays
✅ **Natural flow** - Delays vary within range for authenticity
✅ **Quick setup** - Convert text to simulation-ready JSON in seconds
✅ **Preview before running** - See the result before starting simulation

## Tips

- Each line should follow the format: `Name: Message`
- Names can contain letters, numbers, and spaces
- The name must match the session names in your bot for the simulation to work
- Empty lines are automatically skipped
- All delays and typing durations are randomized within your selected range
