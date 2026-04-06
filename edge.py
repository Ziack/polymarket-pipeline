from __future__ import annotations

import logging
from dataclasses import dataclass

import config
from markets import Market
from classifier import Classification
from news_stream import NewsEvent

log = logging.getLogger(__name__)


@dataclass
class Signal:
    market: Market
    claude_score: float
    market_price: float
    edge: float
    side: str  # "YES" or "NO"
    bet_amount: float
    reasoning: str
    headlines: str
    # V2 fields
    news_source: str = ""
    classification: str = ""
    materiality: float = 0.0
    news_latency_ms: int = 0
    classification_latency_ms: int = 0
    total_latency_ms: int = 0


def detect_edge(
    market: Market,
    claude_score: float,
    reasoning: str = "",
    headlines: str = "",
) -> Signal | None:
    """V1: Compare Claude's confidence against market price."""
    market_price = market.yes_price
    edge = claude_score - market_price

    if abs(edge) < config.EDGE_THRESHOLD:
        return None

    if edge > 0:
        side = "YES"
        raw_edge = edge
    else:
        side = "NO"
        raw_edge = abs(edge)

    bet_amount = size_position(raw_edge)

    return Signal(
        market=market,
        claude_score=claude_score,
        market_price=market_price,
        edge=raw_edge,
        side=side,
        bet_amount=bet_amount,
        reasoning=reasoning,
        headlines=headlines,
    )


def detect_edge_v2(
    market: Market,
    classification: Classification,
    news_event: NewsEvent,
) -> Signal | None:
    """
    V2: Use classification direction + probability/materiality for edge detection.
    Uses direct probability estimate when available; falls back to materiality-based calc.
    Only generates a signal when:
    - Direction is bullish or bearish (not neutral)
    - Materiality meets threshold
    - Computed edge exceeds EDGE_THRESHOLD
    - Market price has room to move in predicted direction
    """
    market_q = f'"{market.question[:50]}"'

    if classification.direction == "neutral":
        log.debug(f"[edge] SKIP neutral — {market_q}")
        return None

    if classification.materiality < config.MATERIALITY_THRESHOLD:
        log.debug(
            f"[edge] SKIP low materiality {classification.materiality:.2f} "
            f"< {config.MATERIALITY_THRESHOLD} — {market_q}"
        )
        return None

    market_price = market.yes_price

    if classification.direction == "bullish":
        side = "YES"
        if market_price > 0.85:
            log.debug(f"[edge] SKIP already-high YES price {market_price:.0%} — {market_q}")
            return None
        # Use direct probability estimate when it differs meaningfully from market
        prob = classification.probability
        if abs(prob - market_price) > 0.02:
            edge = prob - market_price
        else:
            edge = classification.materiality * (1.0 - market_price)
    else:  # bearish
        side = "NO"
        if market_price < 0.15:
            log.debug(f"[edge] SKIP already-low YES price {market_price:.0%} — {market_q}")
            return None
        prob = classification.probability
        if abs(prob - market_price) > 0.02:
            edge = market_price - prob
        else:
            edge = classification.materiality * market_price

    if edge < config.EDGE_THRESHOLD:
        log.debug(
            f"[edge] SKIP edge {edge:.1%} < {config.EDGE_THRESHOLD:.0%} "
            f"({side} mat:{classification.materiality:.2f} prob:{classification.probability:.0%} "
            f"mkt:{market_price:.0%}) — {market_q}"
        )
        return None

    bet_amount = size_position(edge)
    total_latency = news_event.latency_ms + classification.latency_ms

    log.info(
        f"[edge] SIGNAL {side} edge:{edge:.1%} mat:{classification.materiality:.2f} "
        f"prob:{classification.probability:.0%} mkt:{market_price:.0%} "
        f"bet:${bet_amount} — {market_q}"
    )

    return Signal(
        market=market,
        claude_score=classification.materiality,
        market_price=market_price,
        edge=edge,
        side=side,
        bet_amount=bet_amount,
        reasoning=classification.reasoning,
        headlines=news_event.headline,
        news_source=news_event.source,
        classification=classification.direction,
        materiality=classification.materiality,
        news_latency_ms=news_event.latency_ms,
        classification_latency_ms=classification.latency_ms,
        total_latency_ms=total_latency,
    )


def size_position(edge: float) -> float:
    """Quarter-Kelly position sizing. Capped at MAX_BET_USD."""
    fraction = edge * 0.25
    bankroll = config.DAILY_LOSS_LIMIT_USD * 10
    raw_size = bankroll * fraction
    return min(max(round(raw_size, 2), 1.0), config.MAX_BET_USD)
