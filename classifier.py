"""
Claude classification engine — replaces probability estimation with direction classification.
Asks "does this news confirm or deny the market question?" instead of "what's the probability?"
"""
from __future__ import annotations

import json
import time
import logging
from dataclasses import dataclass

import anthropic

import config
from markets import Market

log = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

CLASSIFICATION_PROMPT = """You are a prediction market analyst. Evaluate this news against the market question.

## Market Question
{question}

## Current Market Price
YES: {yes_price:.0%} implied probability

## Breaking News
{headline}
Source: {source}

## Task
1. Direction: does this make YES more likely ("bullish"), less likely ("bearish"), or is it irrelevant ("neutral")?
2. Materiality: how strongly does this move the needle? (0.0 = no impact, 1.0 = definitive resolution)
3. Probability: given this news, what probability (0.0–1.0) would you assign to YES resolving?

Respond ONLY with valid JSON — no markdown, no explanation outside the JSON:
{{"direction":"bullish"|"bearish"|"neutral","materiality":<0.0-1.0>,"probability":<0.0-1.0>,"reasoning":"<1 sentence>"}}"""


@dataclass
class Classification:
    direction: str      # "bullish", "bearish", "neutral"
    materiality: float  # 0.0-1.0
    probability: float  # direct probability estimate for YES, 0.0-1.0
    reasoning: str
    latency_ms: int
    model: str


def classify(headline: str, market: Market, source: str = "unknown") -> Classification:
    """Classify a news headline against a market question. Synchronous."""
    start = time.time()

    prompt = CLASSIFICATION_PROMPT.format(
        question=market.question,
        yes_price=market.yes_price,
        headline=headline,
        source=source,
    )

    try:
        response = client.messages.create(
            model=config.CLASSIFICATION_MODEL,
            max_tokens=256,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()

        # Strip markdown code fences if present
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        result = json.loads(text)
        latency = int((time.time() - start) * 1000)

        direction = result.get("direction", "neutral")
        if direction not in ("bullish", "bearish", "neutral"):
            direction = "neutral"

        materiality = max(0.0, min(1.0, float(result.get("materiality", 0))))
        probability = max(0.0, min(1.0, float(result.get("probability", market.yes_price))))

        log.debug(
            f"[classifier] {direction} mat:{materiality:.2f} prob:{probability:.0%} "
            f"(market:{market.yes_price:.0%}) — {result.get('reasoning', '')[:60]}"
        )

        return Classification(
            direction=direction,
            materiality=materiality,
            probability=probability,
            reasoning=result.get("reasoning", ""),
            latency_ms=latency,
            model=config.CLASSIFICATION_MODEL,
        )

    except Exception as e:
        latency = int((time.time() - start) * 1000)
        log.warning(f"[classifier] Error: {e}")
        return Classification(
            direction="neutral",
            materiality=0.0,
            probability=market.yes_price,
            reasoning=f"Classification error: {type(e).__name__}",
            latency_ms=latency,
            model=config.CLASSIFICATION_MODEL,
        )


async def classify_async(headline: str, market: Market, source: str = "unknown") -> Classification:
    """Async wrapper around classify()."""
    import asyncio
    return await asyncio.get_event_loop().run_in_executor(
        None, classify, headline, market, source
    )


if __name__ == "__main__":
    test_market = Market(
        condition_id="test",
        question="Will OpenAI release GPT-5 before August 2026?",
        category="ai",
        yes_price=0.62,
        no_price=0.38,
        volume=500000,
        end_date="2026-08-01",
        active=True,
        tokens=[],
    )

    result = classify(
        headline="OpenAI reportedly testing GPT-5 internally with select partners",
        market=test_market,
        source="The Information",
    )
    print(f"Direction: {result.direction}")
    print(f"Materiality: {result.materiality}")
    print(f"Reasoning: {result.reasoning}")
    print(f"Latency: {result.latency_ms}ms")
