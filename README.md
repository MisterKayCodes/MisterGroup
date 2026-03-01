# MisterGroup V2: Advanced Telegram Automation & Simulation Suite

**MisterGroup V2** is a professional-grade Telegram simulation platform designed to create high-fidelity, autonomous group activity. By leveraging multi-account orchestration, real-time news integration, and a sophisticated sentiment-aware dialogue engine, it transforms empty groups into vibrant, human-active communities.

---

## 🌟 Core Functional Pillars

### 1. Zero-Touch AI News Automation
The heart of MisterGroup V2 is its autonomous news-driven engine. It doesn't just send messages; it conducts conversations based on real-world events.
- **4-Hour Intelligence Cycle**: Every 4 hours, the system fetches the latest headlines from Crypto, Forex, and Stock markets.
- **Sentiment Mapping**: News is analyzed to determine if the local market mood is `Bullish`, `Bearish`, or `Neutral (Steady)`.
- **80-Message Archetypes**: For every news event, the system builds an 80-message dialogue script. This ensures that even long-running conversations never repeat themselves or feel scripted.
- **Persona Consistency**: Unlike basic bots, MisterGroup assigns specific roles to your sessions. "User A" will remain the "Skeptic" or the "Bullish Trader" throughout the entire cycle, maintaining a coherent personality.

### 2. Media Vault & Dynamic Tagging
MisterGroup V2 supports a revolutionary media system that uses "Source Channels" to provide proof for conversations.
- **Source-to-Target Pipeline**: Link a private channel containing your balance/profit screenshots. The bot monitors these and organizes them into categories.
- **Dynamic Variable Tags**:
    - `[BALANCE]`: Automatically attaches an account balance screenshot.
    - `[PROFIT]`: Attaches a specific trade result or profit screenshot.
    - `[DEPOSIT]`: Attaches a fund-top-up proof.
    - `[WITHDRAWAL]`: Attaches a payout/withdrawal success screenshot.
- **Self-Healing Media**: If a session is not in the source channel, the system automatically joins the channel, fetches the requested media, and delivers it to your target group seamlessly.

### 3. The "Synthesizer" Dialogue Engine
The `DynamicGenerator` ensures that no two sentences are ever identical.
- **Massive Vocabulary Expansion**: With over **500+ unique variations** for greetings, agreements, jokes, and AI praises, the "repetition window" is massive.
- **Neural Delay Logic**: Messages aren't sent instantly. They follow a human-like pattern with "Type-Reflection-Send" delays, varying based on sentence length and topic transitions.
- **Random Interjections**: Periodically, the engine skips the template and injects a "spontaneous" short reaction (e.g., *"Wow!"*, *"Spicy market today!"*) to break the pattern and simulate genuine human excitement.

### 4. Enterprise-Grade Security
Security is baked into the "Mouth" of the system to prevent unauthorized access to your automation dashboard.
- **PIN Security Guard**: A mandatory 4-digit PIN (`5135`) is required upon every `/start` command. 
- **Admin Locking**: The bot automatically binds itself to the first Admin ID that authenticates, preventing any other user from even seeing the menu.

---

## 🏛️ System Architecture

MisterGroup V2 follows a strict **Modular Isolation** pattern (Clean Architecture) to ensure stability and ease of expansion.

### **Layer 1: The Logic Core (`core/`)**
The "Brain" of the application. It contains no external dependencies.
- **Calculators**: Handles the math behind typing delays and coordinate processing.
- **Models**: Defines the data blueprints (Conversations, Messages, Market Sentiments).
- **Simulation**: The decision logic that decides *who* speaks *when*.

### **Layer 2: The Service Layer (`services/`)**
The "Worker" layer that handles all external communication.
- **Telegram Coordinator**: Manages Telethon sessions and handles the physical message delivery.
- **News Service**: Fetches real-time JSON news data from external crypto/forex APIs.
- **Automation Worker**: The "Conductor" that pulls news, picks a template, and triggers the simulation.

### **Layer 3: The Data Vault (`data/`)**
The persistent memory of the system.
- **SQLite Repositories**: High-performance, low-latency storage for your sessions, configs, and media indices.
- **Media Repository**: Acts as the "Librarian" for your source-channel screenshots.

### **Layer 4: The Interface (`bot/`)**
The management dashboard built on Aiogram.
- **Routers**: Cleanly separated command handling for Sessions, Media, Settings, and Schedules.
- **Keyboards**: Dynamic, easy-to-use menu system designed for "7-second setups."

---

## 🛠️ Configuration & Deployment

### 1. Prerequisites
- Python 3.10+
- Telegram `API_ID` and `API_HASH` (from my.telegram.org)
- A Telegram Bot Token (from @BotFather)

### 2. Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

### 3. The "Lazy Setup" Workflow
1. **Launch**: `python main.py`
2. **Authenticate**: Send `/start` and enter PIN `5135`.
3. **Add Sessions**: Use the `👥 Sessions` menu to add your bot accounts via phone numbers.
4. **Link Media**: Linked your source channel in `🖼️ Media Vault`.
5. **Enable AI**: Go to `⚙️ Settings`, set your Target Group ID, and toggle `AI Automation` to ON.
6. **Relax**: The system will now run 100% autonomously 24/7.

---

## � Performance & Monitoring
The system includes built-in diagnostics to track the health of your automation:
- **Typing Latency**: Monitor how long it takes for a message to be generated vs. sent.
- **Session Health**: Real-time status icons for every account (Active/Logged Out).
- **Auto-Retry**: If a news fetch fails, the system uses a fallback "Smart Market" topic to keep the conversation flowing.

---

## 🚨 Developer Rules
- **Modular Integrity**: Never import `bot` or `services` into the `core` folder. The logic must remain pure.
- **File Limits**: No single file should exceed **200 lines**. If it grows, split it into specific sub-modules.
- **Maintenance**: Use `python scripts/watchdog_reload.py` for a real-time development experience.

---
**Developed and Maintained by MisterKayCodes 💛**

---

## 🛠️ Setup & Installation

1.  **Clone & Install**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Configure DNA**:
    Rename `.env.example` to `.env` and fill in your `API_ID`, `API_HASH`, and `BOT_TOKEN`.
3.  **Birth the Organism**:
    ```bash
    python main.py
    ```
4.  **Developer Mode**:
    Use the watchdog script for real-time reloads during development:
    ```bash
    python scripts/watchdog_reload.py
    ```

---

## 🚨 Development Guidelines
- **Keep it Lean**: No file should exceed 200 lines.
- **Stay Modular**: Logic belongs in `core/`, UI belongs in `bot/`, and IO belongs in `services/`.
- **Media First**: Always verify your source channel is linked before using `[BALANCE]` tags.

---
**Created with 💛 by Mister**
