# Made by Mister 💛
import aiohttp
import xml.etree.ElementTree as ET
from typing import Dict, Optional
from loguru import logger

class NewsFetcher:
    """The 'Ears' (services/news/). Fetches real-world signals from RSS feeds without API keys."""
    
    FEEDS = {
        "crypto": "https://cointelegraph.com/rss/tag/bitcoin",
        "forex": "https://www.dailyfx.com/feeds/forex-news",
        "stocks": "https://finance.yahoo.com/news/rssindex"
    }

    @classmethod
    async def fetch_latest(cls, category: str = "crypto") -> Optional[Dict[str, str]]:
        """Polls the 'Outside World' for the latest headline and asset."""
        url = cls.FEEDS.get(category, cls.FEEDS["crypto"])
        try:
            head = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0"}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10, headers=head) as response:
                    if response.status != 200: return None
                    text = await response.text()
                    
            root = ET.fromstring(text)
            
            # Auto-Find Item: Supports Item (RSS) or Entry (Atom)
            item = root.find(".//item") or root.find(".//{http://www.w3.org/2005/Atom}entry")
            if item is None: return None
            
            # Find News Node
            t_node = item.find("title") or item.find("{http://www.w3.org/2005/Atom}title")
            d_node = item.find("description") or item.find("{http://www.w3.org/2005/Atom}summary")
            l_node = item.find("link")
            
            title = t_node.text if t_node is not None else "Market News Update"
            description = d_node.text if d_node is not None else ""
            link = l_node.attrib.get('href', '') if l_node is not None and 'href' in l_node.attrib else (l_node.text if l_node is not None else "")
            
            # Simple sentiment & asset extraction logic
            asset = "BTC"
            if "ETH" in title.upper(): asset = "ETH"
            elif "GOLD" in title.upper(): asset = "Gold"
            elif "USD" in title.upper(): asset = "Dollar"
            
            sentiment = "bullish"
            bear_words = ["drop", "fall", "crash", "bear", "dump", "red", "dip", "warn"]
            if any(w in title.lower() or w in description.lower() for w in bear_words):
                sentiment = "bearish"
                
            return {
                "title": title,
                "asset": asset,
                "sentiment": sentiment,
                "link": item.find("link").text
            }
        except Exception as e:
            logger.error(f"News fetch error: {e}")
            return None
