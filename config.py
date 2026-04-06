import os
from dotenv import load_dotenv

load_dotenv()

# --- Anthropic ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# --- Polymarket CLOB ---
POLYMARKET_API_KEY = os.getenv("POLYMARKET_API_KEY", "")
POLYMARKET_API_SECRET = os.getenv("POLYMARKET_API_SECRET", "")
POLYMARKET_API_PASSPHRASE = os.getenv("POLYMARKET_API_PASSPHRASE", "")
POLYMARKET_PRIVATE_KEY = os.getenv("POLYMARKET_PRIVATE_KEY", "")
POLYMARKET_HOST = "https://clob.polymarket.com"
POLYMARKET_WS_HOST = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

# --- Twitter API v2 ---
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

# --- Telegram (Telethon user account — reads any public channel) ---
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_CHANNEL_IDS = [
    c.strip() for c in os.getenv("TELEGRAM_CHANNEL_IDS", "").split(",") if c.strip()
]

# --- NewsAPI (optional, broader coverage) ---
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

# --- RSS Feeds ---
RSS_FEEDS = [
    # AI & Tech
    "https://news.google.com/rss/search?q=AI+artificial+intelligence+OpenAI+Anthropic&hl=en-US&gl=US&ceid=US:en",
    "https://feeds.feedburner.com/TechCrunch",
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "https://www.theverge.com/rss/index.xml",
    # Crypto
    "https://news.google.com/rss/search?q=bitcoin+ethereum+crypto+blockchain&hl=en-US&gl=US&ceid=US:en",
    "https://cointelegraph.com/rss",
    "https://coindesk.com/arc/outboundfeeds/rss/",
    "https://decrypt.co/feed",
    # US Politics & Policy
    "https://news.google.com/rss/search?q=congress+senate+white+house+election&hl=en-US&gl=US&ceid=US:en",
    "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
    "https://rss.politico.com/politics-news.xml",
    # Economics & Finance
    "https://news.google.com/rss/search?q=federal+reserve+interest+rates+inflation+tariff&hl=en-US&gl=US&ceid=US:en",
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    # Geopolitics
    "https://news.google.com/rss/search?q=geopolitics+conflict+war+sanctions&hl=en-US&gl=US&ceid=US:en",
    "https://feeds.reuters.com/reuters/worldNews",
    # Science & Space
    "https://news.google.com/rss/search?q=SpaceX+NASA+space+launch&hl=en-US&gl=US&ceid=US:en",
    # Prediction market meta
    "https://news.google.com/rss/search?q=polymarket+prediction+market+odds&hl=en-US&gl=US&ceid=US:en",
]

# --- Pipeline Settings ---
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
MAX_BET_USD = float(os.getenv("MAX_BET_USD", "25"))
DAILY_LOSS_LIMIT_USD = float(os.getenv("DAILY_LOSS_LIMIT_USD", "100"))
EDGE_THRESHOLD = float(os.getenv("EDGE_THRESHOLD", "0.05"))   # lowered from 0.10
NEWS_LOOKBACK_HOURS = 6

# --- V2 Settings ---
MAX_VOLUME_USD = float(os.getenv("MAX_VOLUME_USD", "500000"))
MIN_VOLUME_USD = float(os.getenv("MIN_VOLUME_USD", "1000"))
MATERIALITY_THRESHOLD = float(os.getenv("MATERIALITY_THRESHOLD", "0.45"))  # lowered from 0.6
SPEED_TARGET_SECONDS = float(os.getenv("SPEED_TARGET_SECONDS", "5"))
CLASSIFICATION_MODEL = "claude-haiku-4-5-20251001"
SCORING_MODEL = "claude-sonnet-4-6-20250514"

# --- Categories to track ---
MARKET_CATEGORIES = [
    "ai",
    "technology",
    "crypto",
    "politics",
    "science",
    "finance",
    "geopolitics",
    "elections",
    "sports",
]

# --- Twitter filter keywords (for filtered stream rules) ---
TWITTER_KEYWORDS = [
    "OpenAI", "GPT-5", "Anthropic", "Claude", "Google AI", "Gemini",
    "Bitcoin", "Ethereum", "Solana", "crypto", "DeFi",
    "Fed rate", "tariff", "Congress", "White House", "Senate",
    "SpaceX", "Starship", "NASA",
    "Apple", "NVIDIA", "Microsoft", "Google",
    "election", "war", "sanctions", "ceasefire",
]
