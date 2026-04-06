"""
Real-time news monitor — event-driven architecture.
Sources: Twitter API v2 filtered stream, Telegram channels (Telethon), RSS fallback.
Emits NewsEvent objects into an asyncio queue as breaking news arrives.
"""
from __future__ import annotations

import asyncio
import re
import time
import logging
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

import httpx

import config
from scraper import scrape_all, NewsItem

log = logging.getLogger(__name__)


@dataclass
class NewsEvent:
    headline: str
    source: str  # "twitter", "telegram", "rss"
    url: str
    received_at: datetime
    published_at: datetime
    summary: str = ""
    raw_data: dict = field(default_factory=dict)
    latency_ms: int = 0  # time from publication to our receipt

    def age_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self.received_at).total_seconds()


class TwitterStream:
    """Twitter API v2 filtered stream for real-time keyword monitoring."""

    def __init__(self, bearer_token: str, keywords: list[str]):
        self.bearer_token = bearer_token
        self.keywords = keywords
        self.base_url = "https://api.twitter.com/2"
        self.enabled = bool(bearer_token)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.bearer_token}"}

    async def setup_rules(self):
        """Set up filtered stream rules based on keywords."""
        if not self.enabled:
            return

        async with httpx.AsyncClient() as client:
            # Get existing rules
            resp = await client.get(
                f"{self.base_url}/tweets/search/stream/rules",
                headers=self._headers(),
                timeout=10,
            )
            existing = resp.json().get("data", [])

            # Delete existing rules
            if existing:
                ids = [r["id"] for r in existing]
                await client.post(
                    f"{self.base_url}/tweets/search/stream/rules",
                    headers=self._headers(),
                    json={"delete": {"ids": ids}},
                    timeout=10,
                )

            # Create new rules from keywords (max 25 chars per rule for Basic)
            rules = []
            # Batch keywords into OR groups
            batch_size = 5
            for i in range(0, len(self.keywords), batch_size):
                batch = self.keywords[i:i + batch_size]
                value = " OR ".join(f'"{kw}"' for kw in batch)
                rules.append({"value": value, "tag": f"batch_{i // batch_size}"})

            if rules:
                await client.post(
                    f"{self.base_url}/tweets/search/stream/rules",
                    headers=self._headers(),
                    json={"add": rules[:5]},  # Basic tier: 5 rules max
                    timeout=10,
                )

    async def stream(self, queue: asyncio.Queue):
        """Connect to filtered stream and emit NewsEvents."""
        if not self.enabled:
            log.info("[twitter] No bearer token — stream disabled")
            return

        try:
            await self.setup_rules()
        except Exception as e:
            log.warning(f"[twitter] Failed to setup rules: {e}")
            return

        backoff = 1
        while True:
            try:
                async with httpx.AsyncClient() as client:
                    async with client.stream(
                        "GET",
                        f"{self.base_url}/tweets/search/stream",
                        headers=self._headers(),
                        params={"tweet.fields": "created_at,author_id,text"},
                        timeout=None,
                    ) as resp:
                        backoff = 1
                        async for line in resp.aiter_lines():
                            if not line.strip():
                                continue
                            try:
                                import json
                                data = json.loads(line)
                                tweet = data.get("data", {})
                                text = tweet.get("text", "")
                                created = tweet.get("created_at", "")

                                now = datetime.now(timezone.utc)
                                try:
                                    pub = datetime.fromisoformat(created.replace("Z", "+00:00"))
                                    latency = int((now - pub).total_seconds() * 1000)
                                except (ValueError, AttributeError):
                                    pub = now
                                    latency = 0

                                event = NewsEvent(
                                    headline=text[:280],
                                    source="twitter",
                                    url=f"https://twitter.com/i/status/{tweet.get('id', '')}",
                                    received_at=now,
                                    published_at=pub,
                                    latency_ms=latency,
                                    raw_data=data,
                                )
                                await queue.put(event)
                            except Exception as e:
                                log.debug(f"[twitter] Parse error: {e}")

            except (httpx.HTTPError, Exception) as e:
                log.warning(f"[twitter] Stream error: {e}, reconnecting in {backoff}s")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)


class TelegramMonitor:
    """Monitor Telegram channels via Telethon user account.
    Reads any public channel without needing admin or bot membership.
    """

    # Price alert pattern — skip messages that are purely price data
    _PRICE_ALERT_RE = re.compile(r"^[\$€£¥]?\d[\d,\.]+\s*[A-Z]{2,5}\b")

    def __init__(self, api_id: int, api_hash: str, channel_ids: list[str]):
        self.api_id = api_id
        self.api_hash = api_hash
        self.channel_ids = channel_ids
        self.enabled = bool(api_id) and bool(api_hash) and bool(channel_ids)
        self._session_path = "telegram_session"

    async def stream(self, queue: asyncio.Queue):
        """Connect via Telethon and emit NewsEvents for every new channel message."""
        if not self.enabled:
            log.info("[telegram] No API credentials or channels — monitor disabled")
            return

        try:
            from telethon import TelegramClient, events as tg_events
        except ImportError:
            log.warning("[telegram] telethon not installed — run: pip install telethon")
            return

        # Accept both numeric IDs (-100XXXXXXX) and @usernames
        channel_entities: list = []
        for cid in self.channel_ids:
            cid = cid.strip()
            if not cid:
                continue
            try:
                channel_entities.append(int(cid))
            except ValueError:
                channel_entities.append(cid.lstrip("@"))

        backoff = 5
        while True:
            try:
                client = TelegramClient(self._session_path, self.api_id, self.api_hash)
                await client.start()

                @client.on(tg_events.NewMessage(chats=channel_entities))
                async def handler(event):
                    text = (event.message.message or "").strip()

                    # Noise filters
                    if len(text) < 25:
                        return
                    if self._PRICE_ALERT_RE.match(text[:40]):
                        return
                    # Skip pure forwards with no caption
                    if event.message.fwd_from is not None and not text:
                        return

                    now = datetime.now(timezone.utc)
                    msg_date = event.message.date
                    if msg_date is not None and msg_date.tzinfo is None:
                        msg_date = msg_date.replace(tzinfo=timezone.utc)
                    pub = msg_date or now
                    latency = int((now - pub).total_seconds() * 1000)

                    news_event = NewsEvent(
                        headline=text[:500],
                        source="telegram",
                        url="",
                        received_at=now,
                        published_at=pub,
                        latency_ms=latency,
                        raw_data={"chat_id": str(event.chat_id)},
                    )
                    await queue.put(news_event)
                    log.debug(f"[telegram] ({latency}ms) {text[:80]}")

                log.info(f"[telegram] Connected — monitoring {len(channel_entities)} channels")
                backoff = 5
                await client.run_until_disconnected()

            except Exception as e:
                log.warning(f"[telegram] Error: {e}, reconnecting in {backoff}s")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 120)


class RSSFallback:
    """Periodic RSS scraping as a fallback news source."""

    def __init__(self, interval_seconds: float = 120):
        self.interval = interval_seconds
        self._seen_headlines: set[str] = set()

    async def stream(self, queue: asyncio.Queue):
        """Poll RSS feeds periodically and emit new headlines."""
        while True:
            try:
                items = await asyncio.get_event_loop().run_in_executor(
                    None, scrape_all
                )
                now = datetime.now(timezone.utc)
                new_count = 0

                for item in items:
                    key = item.headline.lower()[:80]
                    if key in self._seen_headlines:
                        continue
                    self._seen_headlines.add(key)
                    new_count += 1

                    latency = int((now - item.published_at).total_seconds() * 1000)

                    event = NewsEvent(
                        headline=item.headline,
                        source="rss",
                        url=item.url,
                        received_at=now,
                        published_at=item.published_at,
                        summary=item.summary,
                        latency_ms=latency,
                    )
                    await queue.put(event)

                if new_count:
                    log.info(f"[rss] {new_count} new headlines")

                # Trim seen cache
                if len(self._seen_headlines) > 5000:
                    self._seen_headlines = set(list(self._seen_headlines)[-2000:])

            except Exception as e:
                log.warning(f"[rss] Error: {e}")

            await asyncio.sleep(self.interval)


class NewsAggregator:
    """Runs all news sources concurrently, deduplicates, emits to output queue."""

    def __init__(self, output_queue: asyncio.Queue):
        self.output_queue = output_queue
        self._internal_queue: asyncio.Queue = asyncio.Queue()
        self._seen: set[str] = set()

        self.twitter = TwitterStream(config.TWITTER_BEARER_TOKEN, config.TWITTER_KEYWORDS)
        self.telegram = TelegramMonitor(
            config.TELEGRAM_API_ID,
            config.TELEGRAM_API_HASH,
            config.TELEGRAM_CHANNEL_IDS,
        )
        self.rss = RSSFallback(interval_seconds=120)

        self.stats = {"twitter": 0, "telegram": 0, "rss": 0, "total": 0, "deduped": 0}

    async def run(self):
        """Start all sources and the dedup router."""
        await asyncio.gather(
            self.twitter.stream(self._internal_queue),
            self.telegram.stream(self._internal_queue),
            self.rss.stream(self._internal_queue),
            self._dedup_router(),
            return_exceptions=True,
        )

    async def _dedup_router(self):
        """Deduplicate and forward events to output queue."""
        while True:
            event = await self._internal_queue.get()
            key = event.headline.lower()[:80]
            if key in self._seen:
                self.stats["deduped"] += 1
                continue

            self._seen.add(key)
            self.stats[event.source] = self.stats.get(event.source, 0) + 1
            self.stats["total"] += 1

            await self.output_queue.put(event)

            if len(self._seen) > 10000:
                self._seen = set(list(self._seen)[-5000:])


if __name__ == "__main__":
    async def _test():
        q: asyncio.Queue = asyncio.Queue()
        agg = NewsAggregator(q)

        async def printer():
            while True:
                event = await q.get()
                print(f"[{event.source}] ({event.latency_ms}ms) {event.headline[:80]}")

        await asyncio.gather(agg.run(), printer())

    asyncio.run(_test())
