#!/usr/bin/env python3
"""Generate the Polymarket Pipeline Setup Guide PDF."""
from __future__ import annotations

from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import os
import sys

# --- Colors ---
BLACK = HexColor("#0A0A0A")
GREEN = HexColor("#00FF41")
CYAN = HexColor("#00E5FF")
DIM_GREEN = HexColor("#1A3A1A")
DARK_PANEL = HexColor("#111111")
PANEL_BORDER = HexColor("#1C3D1C")
WHITE = HexColor("#E0E0E0")
MUTED = HexColor("#777777")
YELLOW = HexColor("#FFD600")
RED = HexColor("#FF4444")

W, H = letter  # 612 x 792


def draw_bg(c):
    c.setFillColor(BLACK)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def draw_panel(c, x, y, w, h, border_color=PANEL_BORDER):
    c.setFillColor(DARK_PANEL)
    c.setStrokeColor(border_color)
    c.setLineWidth(0.5)
    c.roundRect(x, y, w, h, 6, fill=1, stroke=1)


def text(c, x, y, txt, color=WHITE, size=10, font="Helvetica"):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawString(x, y, txt)


def text_wrap(c, x, y, txt, color=WHITE, size=10, font="Helvetica", max_width=480, line_height=14):
    """Draw text with word wrapping. Returns new y position."""
    c.setFillColor(color)
    c.setFont(font, size)
    words = txt.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if c.stringWidth(test, font, size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    for line in lines:
        if y < 60:
            c.showPage()
            draw_bg(c)
            y = H - 60
        c.setFillColor(color)
        c.setFont(font, size)
        c.drawString(x, y, line)
        y -= line_height
    return y


def code_block(c, x, y, lines, width=480):
    """Draw a code block with dark background."""
    line_h = 14
    padding = 10
    block_h = len(lines) * line_h + padding * 2

    if y - block_h < 50:
        c.showPage()
        draw_bg(c)
        y = H - 60

    draw_panel(c, x - 8, y - block_h + 4, width + 16, block_h, border_color=HexColor("#2A2A2A"))

    cy = y - padding
    for line in lines:
        c.setFillColor(GREEN)
        c.setFont("Courier", 9)
        c.drawString(x, cy, line)
        cy -= line_h

    return y - block_h - 8


def heading(c, x, y, txt, color=GREEN, size=18):
    if y < 100:
        c.showPage()
        draw_bg(c)
        y = H - 60
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", size)
    c.drawString(x, y, txt)
    # Underline
    tw = c.stringWidth(txt, "Helvetica-Bold", size)
    c.setStrokeColor(color)
    c.setLineWidth(0.5)
    c.line(x, y - 4, x + tw, y - 4)
    return y - 30


def subheading(c, x, y, txt, color=CYAN, size=13):
    if y < 80:
        c.showPage()
        draw_bg(c)
        y = H - 60
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", size)
    c.drawString(x, y, txt)
    return y - 22


def bullet(c, x, y, txt, color=WHITE, size=10, max_width=460):
    if y < 60:
        c.showPage()
        draw_bg(c)
        y = H - 60
    c.setFillColor(GREEN)
    c.setFont("Helvetica", size)
    c.drawString(x, y, ">")
    y = text_wrap(c, x + 14, y, txt, color=color, size=size, max_width=max_width)
    return y - 2


def separator(c, y):
    c.setStrokeColor(HexColor("#222222"))
    c.setLineWidth(0.5)
    c.line(50, y, W - 50, y)
    return y - 15


def build_pdf(output_path: str):
    c = canvas.Canvas(output_path, pagesize=letter)

    # ===================== PAGE 1: Cover =====================
    draw_bg(c)

    # Top accent line
    c.setStrokeColor(GREEN)
    c.setLineWidth(2)
    c.line(50, H - 40, W - 50, H - 40)

    # Title
    c.setFillColor(GREEN)
    c.setFont("Helvetica-Bold", 36)
    c.drawString(50, H - 120, "POLYMARKET")
    c.drawString(50, H - 165, "PIPELINE")

    # Subtitle
    c.setFillColor(CYAN)
    c.setFont("Helvetica", 14)
    c.drawString(50, H - 200, "SETUP GUIDE")

    # Tagline
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 11)
    c.drawString(50, H - 240, "An AI-powered news scraper that reads real-time headlines,")
    c.drawString(50, H - 256, "scores confidence on Polymarket events using Claude,")
    c.drawString(50, H - 272, "and places bets automatically when it finds edge.")

    # Pipeline diagram
    y = H - 330
    draw_panel(c, 50, y - 50, W - 100, 55)
    c.setFillColor(GREEN)
    c.setFont("Courier", 10)
    c.drawString(70, y - 20, "RSS Feeds  -->  Claude Scoring  -->  Edge Detection  -->  Auto Trade")
    c.setFillColor(MUTED)
    c.setFont("Courier", 8)
    c.drawString(70, y - 38, "5 sources       confidence 0-1      divergence >= 10%     dry-run default")

    # What you get
    y = H - 430
    c.setFillColor(GREEN)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "WHAT YOU GET")
    y -= 28

    items = [
        "Real-time news scraper pulling from 5 RSS feeds",
        "Claude-powered confidence scoring on prediction markets",
        "Automatic edge detection when AI disagrees with the market",
        "Trade execution via Polymarket CLOB API (dry-run by default)",
        "Bloomberg Terminal-style live dashboard",
        "Full SQLite audit trail — every trade, every reasoning chain",
        "One-command setup — running in 2 minutes",
    ]
    for item in items:
        y = bullet(c, 60, y, item)

    # Footer
    c.setStrokeColor(GREEN)
    c.setLineWidth(2)
    c.line(50, 60, W - 50, 60)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(50, 44, "github.com/brodyautomates/polymarket-pipeline")
    c.drawRightString(W - 50, 44, "@brodyautomates")

    c.showPage()

    # ===================== PAGE 2: Prerequisites =====================
    draw_bg(c)
    y = H - 60

    y = heading(c, 50, y, "1. PREREQUISITES")
    y -= 5

    y = subheading(c, 50, y, "What You Need Before Starting")
    y -= 5

    y = bullet(c, 60, y, "Python 3.9 or higher installed on your machine")
    y = bullet(c, 60, y, "An Anthropic API key (get one at console.anthropic.com)")
    y = bullet(c, 60, y, "A terminal app (Terminal, iTerm2, Ghostty, Warp, etc.)")
    y = bullet(c, 60, y, "Git installed (to clone the repo)")

    y -= 10
    y = subheading(c, 50, y, "Optional (for enhanced features)")
    y -= 5

    y = bullet(c, 60, y, "NewsAPI key — broader news coverage beyond RSS (newsapi.org)")
    y = bullet(c, 60, y, "Polymarket API credentials — only needed for live trading")
    y = bullet(c, 60, y, "Python 3.9.10+ — required for the Polymarket CLOB trading client")

    y -= 15
    y = separator(c, y)

    # Check Python version
    y = subheading(c, 50, y, "Check Your Python Version")
    y -= 5

    y = code_block(c, 60, y, [
        "python3 --version",
        "",
        "# If below 3.9, install via Homebrew:",
        "brew install python@3.12",
    ])

    y -= 10
    y = text_wrap(c, 50, y, "If you see Python 3.9.x or higher, you're good. The pipeline works on 3.9+. For live trading via Polymarket's API, you need 3.9.10 or higher.", color=MUTED, size=9, max_width=500)

    y -= 15
    y = separator(c, y)

    # Get Anthropic key
    y = subheading(c, 50, y, "Get Your Anthropic API Key")
    y -= 5

    steps = [
        "Go to console.anthropic.com and sign in (or create an account)",
        "Navigate to API Keys in the left sidebar",
        "Click 'Create Key' and copy the key (starts with sk-ant-...)",
        "Keep this key — you'll enter it during setup",
    ]
    for i, step in enumerate(steps):
        y = bullet(c, 60, y, f"Step {i+1}: {step}")

    # Footer
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(50, 35, "Polymarket Pipeline — Setup Guide")
    c.drawRightString(W - 50, 35, "Page 2")

    c.showPage()

    # ===================== PAGE 3: Installation =====================
    draw_bg(c)
    y = H - 60

    y = heading(c, 50, y, "2. INSTALLATION")
    y -= 5

    y = subheading(c, 50, y, "Option A: One-Command Setup (Recommended)")
    y -= 5

    y = text_wrap(c, 50, y, "This script handles everything — virtual environment, dependencies, API key entry, and verification.", color=MUTED, size=9)
    y -= 8

    y = code_block(c, 60, y, [
        "git clone https://github.com/brodyautomates/polymarket-pipeline.git",
        "cd polymarket-pipeline",
        "bash setup.sh",
    ])

    y -= 5
    y = text_wrap(c, 50, y, "The setup script will walk you through entering your API keys interactively. Just paste them when prompted.", color=WHITE, size=10)

    y -= 15
    y = separator(c, y)

    y = subheading(c, 50, y, "Option B: Manual Setup")
    y -= 5

    y = code_block(c, 60, y, [
        "git clone https://github.com/brodyautomates/polymarket-pipeline.git",
        "cd polymarket-pipeline",
        "python3 -m venv .venv",
        "source .venv/bin/activate",
        "pip install -r requirements.txt",
        "cp .env.example .env",
    ])

    y -= 5
    y = text_wrap(c, 50, y, "Then open .env in any text editor and add your keys:", color=WHITE, size=10)
    y -= 8

    y = code_block(c, 60, y, [
        "# Required",
        "ANTHROPIC_API_KEY=sk-ant-your-key-here",
        "",
        "# Optional — broader news coverage",
        "NEWSAPI_KEY=your-newsapi-key",
        "",
        "# Optional — only for live trading",
        "POLYMARKET_API_KEY=your-key",
        "POLYMARKET_API_SECRET=your-secret",
        "POLYMARKET_API_PASSPHRASE=your-passphrase",
        "POLYMARKET_PRIVATE_KEY=your-private-key",
    ])

    y -= 15
    y = separator(c, y)

    y = subheading(c, 50, y, "Verify Your Setup")
    y -= 5

    y = text_wrap(c, 50, y, "Run the verify command to check every connection before you start:", color=WHITE, size=10)
    y -= 8

    y = code_block(c, 60, y, [
        "python cli.py verify",
    ])

    y -= 5
    y = text_wrap(c, 50, y, "This checks: Python version, dependencies, .env file, Anthropic API key, news scraper, Polymarket API, and SQLite database. Fix anything marked FAIL before continuing.", color=MUTED, size=9, max_width=500)

    # Footer
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(50, 35, "Polymarket Pipeline — Setup Guide")
    c.drawRightString(W - 50, 35, "Page 3")

    c.showPage()

    # ===================== PAGE 4: Running the Pipeline =====================
    draw_bg(c)
    y = H - 60

    y = heading(c, 50, y, "3. RUNNING THE PIPELINE")
    y -= 5

    y = subheading(c, 50, y, "Your First Run (Dry-Run Mode)")
    y -= 5

    y = text_wrap(c, 50, y, "Dry-run is the default. The pipeline scans real markets, scores with Claude, detects edge — but logs trades instead of placing them. Zero risk.", color=WHITE, size=10)
    y -= 8

    y = code_block(c, 60, y, [
        "source .venv/bin/activate",
        "python cli.py run",
    ])

    y -= 5
    y = text_wrap(c, 50, y, "You'll see the pipeline scrape headlines, fetch Polymarket markets, score each one with Claude, and log any signals it finds.", color=MUTED, size=9, max_width=500)

    y -= 15

    y = subheading(c, 50, y, "Customize Your Run")
    y -= 5

    y = code_block(c, 60, y, [
        "# Scan more markets, look further back for news",
        "python cli.py run --max 15 --hours 12",
        "",
        "# Lower the edge threshold (more signals, less conviction)",
        "python cli.py run --threshold 0.08",
        "",
        "# Enable live trading (requires Polymarket credentials)",
        "python cli.py run --live",
    ])

    y -= 15

    y = subheading(c, 50, y, "Launch the Live Dashboard")
    y -= 5

    y = text_wrap(c, 50, y, "Full-screen terminal dashboard showing the pipeline in real-time. Market scanner, trade log, performance stats, news ticker — all updating live.", color=WHITE, size=10)
    y -= 8

    y = code_block(c, 60, y, [
        "python cli.py dashboard",
        "",
        "# Faster scan cycles (every 30 seconds)",
        "python cli.py dashboard --speed 30",
    ])

    y -= 15
    y = separator(c, y)

    y = subheading(c, 50, y, "All CLI Commands")
    y -= 5

    commands = [
        ("python cli.py verify", "Check all API keys and connections"),
        ("python cli.py run", "Run full pipeline (dry-run default)"),
        ("python cli.py run --live", "Enable real trading"),
        ("python cli.py dashboard", "Launch live terminal dashboard"),
        ("python cli.py scrape", "Test the news scraper"),
        ("python cli.py markets", "Browse active Polymarket markets"),
        ("python cli.py trades", "View your trade log"),
        ("python cli.py stats", "Performance statistics"),
    ]

    for cmd, desc in commands:
        if y < 60:
            c.showPage()
            draw_bg(c)
            y = H - 60
        c.setFillColor(GREEN)
        c.setFont("Courier", 9)
        c.drawString(60, y, cmd)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 9)
        c.drawString(310, y, desc)
        y -= 16

    # Footer
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(50, 35, "Polymarket Pipeline — Setup Guide")
    c.drawRightString(W - 50, 35, "Page 4")

    c.showPage()

    # ===================== PAGE 5: How It Works =====================
    draw_bg(c)
    y = H - 60

    y = heading(c, 50, y, "4. HOW IT WORKS")
    y -= 5

    sections = [
        ("News Scraping", "scraper.py",
         "Pulls headlines from 5 RSS feeds — Google News (AI), TechCrunch, Ars Technica, The Verge, NYT Technology. Optional NewsAPI integration for broader coverage. Deduplicates by headline similarity, filters by recency (default: last 6 hours)."),

        ("Market Fetching", "markets.py",
         "Fetches active markets from Polymarket's Gamma API, sorted by trading volume. Categorizes each market into AI, crypto, politics, technology, or science by keyword matching on the question text."),

        ("Confidence Scoring", "scorer.py",
         "For each market, filters relevant headlines and sends them to Claude with a calibrated prompt. Claude returns an independent probability estimate (0.0-1.0) and reasoning. The prompt explicitly prevents anchoring to the current market price."),

        ("Edge Detection", "edge.py",
         "Compares Claude's confidence against the market's implied probability (YES token price). If they diverge by more than the threshold (default 10%), that's a trade signal. Position sizing uses quarter-Kelly criterion — conservative enough to survive variance."),

        ("Trade Execution", "executor.py",
         "In dry-run mode: logs what it would have bet. In live mode: places limit orders through Polymarket's CLOB API. Safety rails enforce max bet ($25), daily loss limit ($100), and auto-halt on breach."),

        ("Logging", "logger.py",
         "Every signal is logged to SQLite — market question, Claude's score, market price, edge, side, amount, reasoning, and the headlines that informed the decision. Full audit trail."),
    ]

    for title, filename, desc in sections:
        if y < 120:
            c.showPage()
            draw_bg(c)
            y = H - 60

        c.setFillColor(CYAN)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, title)
        c.setFillColor(MUTED)
        c.setFont("Courier", 9)
        c.drawString(250, y, filename)
        y -= 18
        y = text_wrap(c, 50, y, desc, color=WHITE, size=9.5, max_width=510, line_height=13)
        y -= 12

    # Footer
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(50, 35, "Polymarket Pipeline — Setup Guide")
    c.drawRightString(W - 50, 35, "Page 5")

    c.showPage()

    # ===================== PAGE 6: Configuration & Safety =====================
    draw_bg(c)
    y = H - 60

    y = heading(c, 50, y, "5. CONFIGURATION & SAFETY")
    y -= 5

    y = subheading(c, 50, y, "Settings (.env)")
    y -= 5

    settings = [
        ("DRY_RUN", "true", "Set to false for live trading"),
        ("MAX_BET_USD", "25", "Maximum single bet size in dollars"),
        ("DAILY_LOSS_LIMIT_USD", "100", "Pipeline halts if daily losses hit this"),
        ("EDGE_THRESHOLD", "0.10", "Minimum AI-vs-market divergence to trigger trade"),
    ]

    # Table header
    c.setFillColor(GREEN)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(60, y, "SETTING")
    c.drawString(240, y, "DEFAULT")
    c.drawString(330, y, "DESCRIPTION")
    y -= 5
    c.setStrokeColor(HexColor("#333333"))
    c.line(60, y, W - 60, y)
    y -= 15

    for setting, default, desc in settings:
        c.setFillColor(GREEN)
        c.setFont("Courier", 9)
        c.drawString(60, y, setting)
        c.setFillColor(WHITE)
        c.setFont("Courier", 9)
        c.drawString(240, y, default)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 9)
        c.drawString(330, y, desc)
        y -= 18

    y -= 15
    y = subheading(c, 50, y, "Safety Rails")
    y -= 5

    safety = [
        "Dry-run mode is ON by default. Zero real trades until you explicitly enable --live.",
        "$25 max single bet. Configurable, but you have to change it intentionally.",
        "$100 daily loss limit. Pipeline stops executing if you hit this.",
        "Quarter-Kelly position sizing. Conservative sizing that survives bad streaks.",
        "API keys never leave your machine. .env is gitignored. Nothing sent anywhere except the APIs you configure.",
    ]
    for item in safety:
        y = bullet(c, 60, y, item, max_width=470)

    y -= 15
    y = separator(c, y)

    y = subheading(c, 50, y, "RSS Feeds (config.py)")
    y -= 5

    y = text_wrap(c, 50, y, "The default feeds are configured in config.py. You can add, remove, or swap them:", color=WHITE, size=10)
    y -= 8

    y = code_block(c, 60, y, [
        "RSS_FEEDS = [",
        '    "https://news.google.com/rss/search?q=AI...",',
        '    "https://feeds.feedburner.com/TechCrunch",',
        '    "https://feeds.arstechnica.com/arstechnica/...",',
        '    "https://www.theverge.com/rss/index.xml",',
        '    "https://rss.nytimes.com/services/xml/rss/...",',
        "]",
    ])

    # Footer
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(50, 35, "Polymarket Pipeline — Setup Guide")
    c.drawRightString(W - 50, 35, "Page 6")

    c.showPage()

    # ===================== PAGE 7: What You Can Build =====================
    draw_bg(c)
    y = H - 60

    y = heading(c, 50, y, "6. WHAT YOU CAN BUILD FROM HERE")
    y -= 5

    y = text_wrap(c, 50, y, "This is a working foundation. The pipeline is modular — every component can be extended or swapped independently.", color=WHITE, size=10)
    y -= 10

    ideas = [
        ("Add More News Sources", "Reddit API, Twitter/X API, Telegram channels, SEC filings, press release wires. More data = better scoring."),
        ("Smarter Scoring", "Feed Claude the full article text instead of just headlines. Use web scraping to pull article bodies from the URLs."),
        ("Multi-Model Consensus", "Score with Claude + GPT-4 + Gemini. Only bet when all three agree. Reduces false signals dramatically."),
        ("Portfolio Tracking", "Monitor open positions, track resolution status, auto-exit when edge disappears or market moves against you."),
        ("Cron Job Automation", "Run the pipeline every hour automatically. Set it and forget it. crontab -e or use a task scheduler."),
        ("Backtest Engine", "Score historical markets against historical news. Measure calibration. Find out if your edge is real before risking money."),
    ]

    for title, desc in ideas:
        if y < 80:
            c.showPage()
            draw_bg(c)
            y = H - 60
        c.setFillColor(CYAN)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, title)
        y -= 16
        y = text_wrap(c, 50, y, desc, color=MUTED, size=9.5, max_width=510, line_height=13)
        y -= 12

    y -= 15
    y = separator(c, y)

    # Quick reference
    y = subheading(c, 50, y, "Quick Reference — File Map")
    y -= 5

    files = [
        ("scraper.py", "News ingestion — RSS feeds + NewsAPI"),
        ("markets.py", "Polymarket market data — Gamma API"),
        ("scorer.py", "Claude confidence scoring engine"),
        ("edge.py", "Edge detection + Kelly position sizing"),
        ("executor.py", "Trade execution — dry-run + live"),
        ("logger.py", "SQLite trade log + performance"),
        ("pipeline.py", "Full pipeline orchestrator"),
        ("dashboard.py", "Live terminal dashboard"),
        ("cli.py", "CLI interface (run, verify, etc.)"),
        ("config.py", "All settings and thresholds"),
        ("setup.sh", "One-command setup script"),
    ]

    for fname, desc in files:
        if y < 50:
            c.showPage()
            draw_bg(c)
            y = H - 60
        c.setFillColor(GREEN)
        c.setFont("Courier", 9)
        c.drawString(60, y, fname)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 9)
        c.drawString(200, y, desc)
        y -= 15

    # Bottom CTA
    y -= 20
    c.setStrokeColor(GREEN)
    c.setLineWidth(2)
    c.line(50, y, W - 50, y)
    y -= 30
    c.setFillColor(GREEN)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "READY TO RUN")
    y -= 22
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 11)
    c.drawString(50, y, "source .venv/bin/activate && python cli.py run")

    # Footer
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(50, 35, "Polymarket Pipeline — Setup Guide")
    c.drawRightString(W - 50, 35, "Page 7")
    c.drawCentredString(W / 2, 35, "github.com/brodyautomates/polymarket-pipeline")

    c.save()


if __name__ == "__main__":
    # Generate to both locations
    repo_path = os.path.join(os.path.dirname(__file__), "SETUP_GUIDE.pdf")
    desktop_path = os.path.expanduser("~/Desktop/Polymarket_Pipeline_Setup_Guide.pdf")

    build_pdf(repo_path)
    print(f"Generated: {repo_path}")

    build_pdf(desktop_path)
    print(f"Generated: {desktop_path}")
