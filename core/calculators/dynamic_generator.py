# Made by Mister 💛
import random
from typing import List, Dict

class DynamicGenerator:
    """The 'Synthesizer' (core/calculators/). Generates diverse human-like text variations."""

    VARIANTS = {
        "greeting": [
            "Hey guys", "Morning all", "Yo", "Hello everyone", "What's up", "Hi team", "Good day", "Checking in",
            "Anyone see this?", "Mister in the house 💛", "Blessings everyone", "Let's get it today", "How's the group doing?",
            "Up and early", "Good afternoon", "Evening folks", "Is it time yet?", "Watching the clock", "Hope you're all green",
            "Morning legends", "Yo yo!", "Hello world", "Back for more", "Ready to print?", "Hey fam", "What a day!",
            "Checking the pulse", "How we feeling?", "Excited for today", "Let's win", "Greetings masters", "Anyone awake?",
            "Always a pleasure", "Ready for action", "Looking sharp team", "The grind continues", "Morning champions",
            "Yo, market is wild", "Hi everyone, let's win", "What's the word?", "Checking in for duty", "Mister's army is here",
            "Let's make some noise", "Checking from the beach", "Trading from the car today", "Coffee in hand, AI ready"
        ],
        "agreement": [
            "Totally agree", "Exactly", "Spot on", "100%", "You nailed it", "Couldn't agree more", "Facts", "Same here",
            "I was just thinking that", "Pure gold", "Absolutely", "Right on", "No doubt", "For real", "Preach!",
            "My thoughts exactly", "Correct", "Indeed", "I'm with you", "Tell me about it", "Exactly my point",
            "True story", "Couldn't have said it better", "You're reading my mind", "This is the way", "Big facts",
            "Spot on analysis", "Agreed 🥂", "I'm on the same page", "Undisputed", "Exactly what I saw", "You're onto something",
            "Couldn't agree less with the bears", "Exactly! Let's go", "True and real", "Facts only", "Vouching for this",
            "You're a genius", "Precisely", "Word for word", "Matched my view perfectly", "On it 100%"
        ],
        "disagreement": [
            "Not so sure", "Hmm, maybe not", "I disagree", "Doubt it", "Wait, really?", "I have my doubts", "Seems unlikely",
            "Let's be cautious", "The chart says otherwise", "I'm skeptical", "Could be a trap", "I'd wait",
            "Don't buy the hype", "Seems too good", "I'm playing it safe", "Not feeling this one", "I'll pass",
            "Wait for confirmation", "Risky move", "I'm staying on the sidelines", "Too volatile for me",
            "I'd watch out", "Be careful there", "I'm not convinced", "Show me the proof", "Doubtful",
            "Seems like a fakeout", "I'm seeing red flags", "Let's wait for the close", "Unlikely scenario",
            "I'm leaning the other way", "Hmm, I'm divided", "Let's see if it holds", "Don't rush in"
        ],
        "asset": ["BTC", "ETH", "Gold", "USD/JPY", "S&P 500", "Solana", "XAUUSD", "EURAUD", "BNB", "XRP", "DOGE", "ADA", "DOT", "MATIC", "LINK", "AVAX", "LTC", "AUD/USD", "GBP/JPY", "EUR/USD", "Silver", "Oil", "Nasdaq"],
        "action": ["pump", "dump", "breakout", "reversal", "correction", "rally", "squeeze", "dip", "sideways move", "bounce", "rejection", "consolidation", "sweep", "expansion", "crash", "moon shot", "wick", "order flow move"],
        "sentiment_pos": ["looking bullish", "going to the moon", "strong buy", "healthy trend", "massive potential", "heating up", "printing money", "unstopabble", "ready to fly", "bullish AF", "super strong", "breaking out", "mooning", "soaring", "climbing high", "explosive", "legendary move"],
        "sentiment_neg": ["looking bearish", "dropping hard", "sell off coming", "weak support", "bloodbath", "crashing", "rekt soon", "falling knife", "dumping hard", "weakness everywhere", "bleeding", "heading to zero", "panic mode", "bloody market", "bear trap", "ugly chart"],
        "ai_praise": [
            "The AI called it!", "Algorithm is genius", "Quant engine is printing", "Best system yet", "Automation wins again",
            "AI trading is the only way now", "Mister's bot is literally a cheat code", "Just set it and forget it",
            "AI found the trend before anyone", "This AI has better eyes than me", "Earning while I sleep is the dream",
            "Passive income machine confirmed", "Quant power is unreal", "Math never lies", "AI > Manual traders",
            "The system is untouchable", "Best investment I've made", "AI logic is 10 steps ahead", "Pure mathematical edge",
            "Look at the accuracy!", "AI is a monster", "The bot doesn't have emotions, that's why it wins", "In AI we trust",
            "Mister's creation is a goldmine", "The quant engine is on fire", "Best signals ever", "AI is a cheat code",
            "No more staring at charts all day", "The bot is a beast", "Automation for the win", "Consistency is King with AI",
            "I'm never going back to manual", "AI magic", "Quant genius", "Best dev team ever", "Mister Group for life"
        ],
        "joke": [
            "My manual trades are crying 😂", "Retiring soon at this rate", "Bot does the work, I drink coffee",
            "RIP retail traders", "Manual trading is so 2020", "Who needs a job when you have AI?",
            "I forgot how to use a chart 😂 AI is enough", "Banks hate this bot lol", "Wife thinks I'm working hard, I'm just watching the bot",
            "My boss is going to wonder where I went lol", "Imagine still using indicators from 1990 😂", "Bot is my new best friend",
            "I'm hiring a personal chef soon thanks to this bot", "Buying a private island at this rate", "Is it illegal to win this much? 😂",
            "My portfolio is up more than my blood pressure", "AI is my sugar daddy", "I should have started this years ago",
            "Manual traders are the exit liquidity 😂", "Lambo soon? No, whole fleet!", "Mister is Santa Claus for traders"
        ],
        "earnings_vibe": [
            "Weekly payout just hit! 💰", "Profits are stacking up nicely", "My portfolio is loving this AI move",
            "Already made more today than all last week", "Can't wait for the next harvest", "The gains are becoming addictive",
            "My bank account is confused 😂", "Stacking those bills", "Green is my favorite color", "Look at that profit line!",
            "AI is feeding the family today", "Refreshing the balance is a hobby now", "Profits for breakfast",
            "This is what freedom looks like", "Wealth building in progress", "Financial target hit early", "Printing press is active"
        ],
        "profit_expression": [
            "Buying that new Rolex soon", "Vacation is booked! 🏝️", "Time to upgrade the house", "Ordering a celebratory steak",
            "New car smells like AI profits", "Paying off the mortgage early", "Shopping spree incoming!", "Invested back into the AI bot",
            "First class only from now on", "Generational wealth being built", "Checking out some real estate", "Treating the family tonight"
        ],
        "market_vibe": [
            "Market is spicy today!", "Tense hours on the charts", "Pure chaos out there, stay safe", "Quiet before the storm",
            "The heat is on", "Atmosphere is electric", "Excitement is through the roof", "Boring day, but AI doesn't care",
            "Volatile as always", "Market is showing its teeth", "Frenzy in the order books", "Calm and steady wins", "The energy is wild"
        ],
        "interjection": ["Wait...", "Look!", "Wow", "Insanity!", "Unbelievable", "No way", "Crazy", "Holy moly", "Speechless", "Bingo!", "Finally!", "Check this out", "Take a look!", "Boom!", "Legendary", "Stunning", "Classic move", "Calculated!", "Simple as that"],
        "filler": ["Wait for it...", "Let's see", "Interesting", "Keep an eye on this", "Wow", "Classic", "Unreal", "Insanity", "I'm speechless", "Calculated move", "Standard procedure", "Standard AI win", "Typical Monday gain", "Business as usual"],
        "verb_move": ["moving", "pushing", "climbing", "diving", "sliding", "jumping", "soaring", "falling", "flying", "tanking", "exploding", "drifting", "surging", "bleeding", "retracing", "pumping"],
        "adverb_speed": ["fast", "quickly", "slowly", "instantly", "suddenly", "steadily", "aggressive", "violently", "slowly but surely", "with force", "silently", "smoothly", "dramatically"],
        "noun_market": ["market", "order flow", "chart", "volume", "liquidity", "structure", "trend", "resistance", "support", "momentum", "volatility", "sentiment", "levels", "data"]
    }

    @classmethod
    def resolve_placeholders(cls, text: str, mapping: Dict[str, str] = None) -> str:
        """Replace [TAGS] or {synonyms} with random variations."""
        mapping = mapping or {}
        
        # 1. Resolve fixed mapping (e.g. Asset name from news)
        for key, val in mapping.items():
            text = text.replace(f"[{key}]", str(val))
            
        # 2. Resolve random variants {variant}
        # We process multiple times to allow nested placeholders if any (though currently simple)
        for _ in range(2): # 2 passes for robustness
            for tag, options in cls.VARIANTS.items():
                placeholder = "{" + tag + "}"
                while placeholder in text:
                    text = text.replace(placeholder, str(random.choice(options)), 1)
        
        return text

    @classmethod
    def generate_variation(cls, base_text: str) -> str:
        """Create a slightly different version of a sentence using basic synonym swapping logic."""
        # Simple implementation: we use the {variant} system mostly
        return cls.resolve_placeholders(base_text)
