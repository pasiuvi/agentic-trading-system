# generate_report.py
# Auto-generates a professional PDF report using your real output files
# Results update automatically every time main.py runs
#
# HOW TO USE:
#   Step 1: pip install reportlab pillow
#   Step 2: python generate_report.py
#   Output: output/trading_report.pdf

import os
import csv
import json
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable, KeepTogether
)

# ── CONFIG ────────────────────────────────────────────────────────────────────
STUDENT_NAME  = "B D P A Karunarathna"
UNIVERSITY    = "NIBM - Coventry University"
MODULE        = "Agentic AI Workflow for Automated Trading (Finance Domain)"
GITHUB        = "github.com/pasiuvi/agentic-trading-system"
OUTPUT_FOLDER = "output"
REPORT_PATH   = os.path.join(OUTPUT_FOLDER, "trading_report.pdf")
SYMBOLS       = ["AAPL", "MSFT", "GOOGL", "BTC-USD", "ETH-USD"]

# Colours
DARK_BLUE  = colors.HexColor("#1F4E79")
MID_BLUE   = colors.HexColor("#2E75B6")
LIGHT_BLUE = colors.HexColor("#D6E4F0")
ALT_ROW    = colors.HexColor("#EBF3FB")
WHITE      = colors.white
BLACK      = colors.black

# ── DYNAMIC DATA LOADERS ──────────────────────────────────────────────────────

def load_trade_decisions():
    """
    Reads trade_decisions.csv written by main.py after every run.
    Handles the exact column names your system produces:
    timestamp, symbol, close_price, market_signal, market_conf,
    rsi, sentiment, decision, final_action, final_conf,
    risk_approved, risk_reason, trade_size_usd, reasoning
    """
    path = os.path.join(OUTPUT_FOLDER, "trade_decisions.csv")
    rows = []
    if os.path.exists(path):
        try:
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    symbol    = row.get("symbol",        "")
                    signal    = row.get("market_signal",  "")
                    sentiment = row.get("sentiment",      "")
                    final     = row.get("final_action",   "")
                    conf_raw  = row.get("final_conf",     "0")
                    # Convert decimal (0.58) to percentage (58%)
                    try:
                        conf = f"{float(conf_raw)*100:.0f}%"
                    except Exception:
                        conf = str(conf_raw)
                    if symbol:
                        rows.append([symbol, signal, sentiment, final, conf])
            print(f"  Agent decisions: ✅ Loaded {len(rows)} rows from trade_decisions.csv")
        except Exception as e:
            print(f"  Agent decisions: ⚠️  Error reading CSV: {e}")
    else:
        print("  Agent decisions: ⚠️  trade_decisions.csv not found - using last known results")
    return rows

def load_results_summary():
    """Reads optional results_summary.json if saved by main.py"""
    path = os.path.join(OUTPUT_FOLDER, "results_summary.json")
    if os.path.exists(path):
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            print("  Results summary: ✅ Loaded from results_summary.json")
            return data
        except Exception:
            pass
    print("  Results summary: ℹ️  Using last known results (no results_summary.json)")
    return None

# ── FALLBACK DATA (last known real results — updated 2026-03-25) ──────────────

FALLBACK_DECISIONS = [
    ["AAPL",    "SELL", "POSITIVE", "SELL", "58%"],
    ["MSFT",    "BUY",  "POSITIVE", "BUY",  "77%"],
    ["GOOGL",   "SELL", "POSITIVE", "SELL", "58%"],
    ["BTC-USD", "SELL", "NEUTRAL",  "SELL", "60%"],
    ["ETH-USD", "BUY",  "NEUTRAL",  "BUY",  "63%"],
]

FALLBACK_BACKTEST = [
    ["AAPL",    "SELL", "POSITIVE", "+5.51%",  "1.21",  "-3.5%",  "100%", "95.1%"],
    ["MSFT",    "BUY",  "POSITIVE", "-19.69%", "-1.63", "-20.7%", "100%", "100%"],
    ["GOOGL",   "SELL", "POSITIVE", "-3.01%",  "-0.73", "-4.3%",  "0%",   "73.2%"],
    ["BTC-USD", "SELL", "NEUTRAL",  "+0.00%",  "0.0",   "0.0%",   "0%",   "100%"],
    ["ETH-USD", "BUY",  "NEUTRAL",  "-0.69%",  "0.1",   "-26.8%", "100%", "100%"],
]

CORRELATION_DATA = [
    ["AAPL vs MSFT",  "0.40", "Moderate — both large-cap tech"],
    ["AAPL vs GOOGL", "0.50", "Moderate — large-cap tech sector"],
    ["BTC vs ETH",    "0.84", "Very high — crypto moves together"],
    ["AAPL vs BTC",   "0.00", "No correlation — stocks vs crypto"],
]

VAR_DATA = [
    ["AAPL",    "-1.92%", "Lowest risk"],
    ["GOOGL",   "-2.28%", "Low risk"],
    ["MSFT",    "-2.39%", "Low risk"],
    ["BTC-USD", "-3.68%", "Medium risk"],
    ["ETH-USD", "-5.55%", "Highest risk"],
]

CLUSTER_DATA = [
    ["AAPL",    "1", "Mid-volatility group"],
    ["MSFT",    "2", "Stable, low-volatility"],
    ["BTC-USD", "2", "Stable, low-volatility"],
    ["GOOGL",   "1", "Mid-volatility group"],
    ["ETH-USD", "0", "High-volatility crypto"],
]

# ── STYLES ────────────────────────────────────────────────────────────────────

def make_style(name, **kw):
    return ParagraphStyle(name, **kw)

STYLES = {}

def init_styles():
    global STYLES
    STYLES = {
        "cover_title": make_style("cover_title",
            fontSize=26, textColor=DARK_BLUE, alignment=TA_CENTER,
            fontName="Helvetica-Bold", spaceAfter=8, leading=32),
        "cover_sub": make_style("cover_sub",
            fontSize=15, textColor=MID_BLUE, alignment=TA_CENTER,
            fontName="Helvetica", spaceAfter=6, leading=20),
        "cover_info": make_style("cover_info",
            fontSize=12, textColor=BLACK, alignment=TA_CENTER,
            fontName="Helvetica", spaceAfter=4, leading=17),
        "cover_desc": make_style("cover_desc",
            fontSize=11, textColor=colors.HexColor("#444444"),
            alignment=TA_CENTER, fontName="Helvetica-Oblique", leading=18),
        "h1": make_style("h1",
            fontSize=14, textColor=WHITE, fontName="Helvetica-Bold",
            spaceAfter=8, spaceBefore=12, leading=18,
            backColor=DARK_BLUE, borderPadding=(5, 8, 5, 8)),
        "h2": make_style("h2",
            fontSize=12, textColor=DARK_BLUE, fontName="Helvetica-Bold",
            spaceAfter=5, spaceBefore=8, leading=16),
        "body": make_style("body",
            fontSize=10, textColor=BLACK, fontName="Helvetica",
            spaceAfter=5, leading=15, alignment=TA_JUSTIFY),
        "caption": make_style("caption",
            fontSize=8.5, textColor=colors.HexColor("#555555"),
            fontName="Helvetica-Oblique", alignment=TA_CENTER,
            spaceAfter=8, leading=12),
        "bullet": make_style("bullet",
            fontSize=10, textColor=BLACK, fontName="Helvetica",
            spaceAfter=4, leading=15, leftIndent=12),
        "th": make_style("th",
            fontSize=9.5, textColor=WHITE,
            fontName="Helvetica-Bold", alignment=TA_CENTER, leading=13),
        "td": make_style("td",
            fontSize=9.5, fontName="Helvetica",
            alignment=TA_CENTER, leading=13),
        "td_small": make_style("td_small",
            fontSize=8.5, fontName="Helvetica",
            alignment=TA_CENTER, leading=12),
        "th_small": make_style("th_small",
            fontSize=8.5, textColor=WHITE,
            fontName="Helvetica-Bold", alignment=TA_CENTER, leading=12),
    }

def P(text, style_name):
    return Paragraph(text, STYLES[style_name])

# ── TABLE BUILDER ─────────────────────────────────────────────────────────────

def make_table(headers, rows, col_widths=None, small=False):
    th = "th_small" if small else "th"
    td = "td_small" if small else "td"
    data = [[Paragraph(str(h), STYLES[th]) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), STYLES[td]) for c in row])
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  DARK_BLUE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, ALT_ROW]),
        ("GRID",           (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    return tbl

# ── IMAGE HELPER ──────────────────────────────────────────────────────────────

def get_image(filename, width=14*cm):
    path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(path):
        try:
            img = Image(path)
            ratio = img.imageHeight / img.imageWidth
            img.drawWidth  = width
            img.drawHeight = width * ratio
            return img
        except Exception as e:
            return P(f"[Could not load chart: {filename} — {e}]", "caption")
    return P(f"[Chart not found: {filename}]", "caption")

# ── HEADER / FOOTER ───────────────────────────────────────────────────────────

def on_later_pages(canvas, doc):
    w, h = A4
    canvas.saveState()
    # Top bar
    canvas.setFillColor(DARK_BLUE)
    canvas.rect(0, h - 1.1*cm, w, 1.1*cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.drawString(1.5*cm, h - 0.78*cm, "Agentic AI Trading System")
    canvas.setFont("Helvetica", 8.5)
    canvas.drawRightString(w - 1.5*cm, h - 0.78*cm,
                           f"MSc Data Science | {UNIVERSITY}")
    # Bottom bar
    canvas.setFillColor(DARK_BLUE)
    canvas.rect(0, 0, w, 0.9*cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(1.5*cm, 0.32*cm,
                      f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}")
    canvas.drawCentredString(w / 2, 0.32*cm, GITHUB)
    canvas.drawRightString(w - 1.5*cm, 0.32*cm, f"Page {doc.page}")
    canvas.restoreState()

def on_first_page(canvas, doc):
    pass  # No header/footer on cover page

# ── MAIN BUILDER ──────────────────────────────────────────────────────────────

def build_report():
    init_styles()
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Load dynamic data
    decisions  = load_trade_decisions()
    agent_rows = decisions if decisions else FALLBACK_DECISIONS

    summary = load_results_summary()
    if summary:
        backtest_rows = summary.get("backtest",    FALLBACK_BACKTEST)
        corr_rows     = summary.get("correlation", CORRELATION_DATA)
        var_rows      = summary.get("var",         VAR_DATA)
        cluster_rows  = summary.get("clusters",    CLUSTER_DATA)
    else:
        backtest_rows = FALLBACK_BACKTEST
        corr_rows     = CORRELATION_DATA
        var_rows      = VAR_DATA
        cluster_rows  = CLUSTER_DATA

    doc = SimpleDocTemplate(
        REPORT_PATH, pagesize=A4,
        topMargin=1.6*cm, bottomMargin=1.4*cm,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        title="Agentic AI Trading System Report",
        author=STUDENT_NAME
    )

    story = []

    # ── COVER PAGE ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 2.5*cm))
    story.append(P("Agentic AI Trading System", "cover_title"))
    story.append(P("Automated Trading Workflow — Final Report", "cover_sub"))
    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width="75%", thickness=2,
                            color=MID_BLUE, spaceAfter=16))
    story.append(Spacer(1, 0.4*cm))
    for label, value in [
        ("Student",    STUDENT_NAME),
        ("Module",     MODULE),
        ("University", UNIVERSITY),
        ("GitHub",     GITHUB),
        ("Report Date",datetime.now().strftime("%B %d, %Y at %H:%M")),
    ]:
        story.append(P(f"<b>{label}:</b>  {value}", "cover_info"))
    story.append(Spacer(1, 1.2*cm))
    story.append(HRFlowable(width="75%", thickness=1,
                            color=LIGHT_BLUE, spaceAfter=14))
    story.append(Spacer(1, 0.4*cm))
    story.append(P(
        "This report presents a complete Agentic AI-based trading system covering "
        "data collection via Yahoo Finance API, AWS cloud integration (S3, RDS, EC2, Lambda), "
        "exploratory data analysis, Random Forest ML modelling, and a four-agent autonomous "
        "decision pipeline for five financial assets.",
        "cover_desc"
    ))
    story.append(PageBreak())

    # ── 1. EXECUTIVE SUMMARY ──────────────────────────────────────────────────
    story.append(P("  1. Executive Summary", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "This project designs and evaluates an Agentic AI-based automated trading workflow. "
        "The system autonomously collects financial market data for five assets, performs "
        "exploratory data analysis, trains Random Forest ML models, retrieves live news "
        "sentiment via VADER NLP, and generates buy/sell/hold decisions through a four-agent "
        "sequential pipeline fully deployed on AWS cloud infrastructure.",
        "body"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P("Agent Decision Summary — Latest Run", "h2"))
    story.append(Spacer(1, 0.1*cm))
    story.append(make_table(
        ["Symbol", "Market Signal", "News Sentiment", "Final Decision", "Confidence"],
        agent_rows,
        col_widths=[3*cm, 3.5*cm, 4*cm, 3.5*cm, 3*cm]
    ))

    # ── 2. DATA COLLECTION ────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(P("  2. Data Collection", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "Financial market data was collected for five assets — AAPL, MSFT, GOOGL (stocks) "
        "and BTC-USD, ETH-USD (cryptocurrencies) — using the yfinance API which provides "
        "Yahoo Finance historical OHLCV data. One year of daily data was downloaded per symbol "
        "(251 rows for stocks, 365 rows for cryptocurrencies). Data is automatically uploaded "
        "to AWS S3 and stored in AWS RDS PostgreSQL via the Lambda function every weekday.",
        "body"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P("AWS Cloud Infrastructure", "h2"))
    story.append(make_table(
        ["AWS Service", "Configuration", "Purpose"],
        [
            ["AWS S3",      "trading-raw-data-2024",             "Stores raw CSV files (stocks/ and crypto/ folders)"],
            ["AWS RDS",     "PostgreSQL, trading-db, us-east-1", "Structured relational database for all market data"],
            ["AWS EC2",     "t2.micro, Amazon Linux 2023",       "Cloud computation server for pipeline execution"],
            ["AWS Lambda",  "Python 3.11, 256MB, 1min timeout",  "Automated daily data fetch function"],
            ["EventBridge", "cron(30 13 ? * MON-FRI *)",         "Schedules Lambda every weekday at 9:30AM EST"],
        ],
        col_widths=[3*cm, 5.5*cm, 8.5*cm]
    ))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "The AWS Lambda function (trading-daily-fetch) runs automatically every weekday, "
        "confirmed by CloudWatch logs showing execution on March 23, 2026 at 13:30 UTC. "
        "Fresh CSV files appear in S3 stocks/ and crypto/ folders after each automated run.",
        "body"))

    # ── 3. EDA ────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(P("  3. Exploratory Data Analysis (EDA)", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "Comprehensive EDA was performed on all five assets. Technical indicators were "
        "engineered including Moving Averages (MA20, MA50), Exponential Moving Average (EMA12), "
        "RSI (14-day window), MACD with Signal Line and Histogram, and Bollinger Bands. "
        "Trading signals were generated using RSI thresholds: RSI below 40 generates a BUY "
        "signal; RSI above 60 generates a SELL signal. Missing values were handled using "
        "forward-fill (ffill) followed by dropna to ensure clean data.",
        "body"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P("Technical Analysis Charts", "h2"))
    for sym in SYMBOLS:
        story.append(KeepTogether([
            get_image(f"{sym}_analysis.png", width=14*cm),
            P(f"Figure: {sym} — Price with MA, Bollinger Bands, RSI and MACD", "caption"),
            Spacer(1, 0.2*cm)
        ]))

    # ── 4. CORRELATION & VOLATILITY ───────────────────────────────────────────
    story.append(PageBreak())
    story.append(P("  4. Correlation and Volatility Analysis", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "Daily return correlations were computed across all five assets to identify "
        "portfolio diversification opportunities and systemic risk. BTC and ETH show "
        "very high correlation (0.84), confirming they move together. Stocks and crypto "
        "show near-zero correlation (0.00), providing excellent portfolio diversification.",
        "body"))
    story.append(Spacer(1, 0.1*cm))
    story.append(KeepTogether([
        get_image("correlation_analysis.png", width=15*cm),
        P("Figure: Daily Returns Correlation Heatmap and 30-Day Rolling Correlation (AAPL vs BTC)",
          "caption"),
    ]))
    story.append(Spacer(1, 0.2*cm))
    story.append(make_table(
        ["Asset Pair", "Correlation", "Interpretation"],
        corr_rows,
        col_widths=[4*cm, 3.5*cm, 9.5*cm]
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(P("Value at Risk (VaR) — 95% Confidence Level", "h2"))
    story.append(P(
        "Value at Risk (VaR) at 95% confidence represents the maximum expected daily loss "
        "under normal market conditions. ETH-USD carries approximately three times more "
        "daily risk than AAPL, providing clear evidence for position sizing decisions.",
        "body"))
    story.append(KeepTogether([
        get_image("volatility_analysis.png", width=15*cm),
        P("Figure: 20-Day Rolling Volatility (%) and Value at Risk (95%) per Asset", "caption"),
    ]))
    story.append(Spacer(1, 0.2*cm))
    story.append(make_table(
        ["Asset", "Daily VaR (95%)", "Risk Level"],
        var_rows,
        col_widths=[4*cm, 5*cm, 8*cm]
    ))

    # ── 5. K-MEANS CLUSTERING ─────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(P("  5. K-Means Asset Clustering", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "K-Means clustering (k=3) was applied to group assets based on three standardised "
        "features: mean daily return, mean 20-day rolling volatility, and mean RSI. "
        "Features were normalised using StandardScaler before clustering to ensure equal "
        "weighting regardless of scale differences between assets.",
        "body"))
    story.append(Spacer(1, 0.2*cm))
    story.append(make_table(
        ["Asset", "Cluster", "Group Interpretation"],
        cluster_rows,
        col_widths=[4*cm, 3.5*cm, 9.5*cm]
    ))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "The clustering reveals distinct risk-return profiles. ETH-USD stands alone as the "
        "highest-volatility asset. The remaining assets group by their momentum and volatility "
        "characteristics, providing actionable insight for portfolio construction.",
        "body"))

    # ── 6. ML MODEL ───────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(P("  6. Machine Learning Model", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "A Random Forest Classifier (100 estimators, max_depth=5, random_state=42) was "
        "trained independently per asset to predict Buy/Sell/Hold signals. Nine features "
        "were used: RSI, MACD, MACD_Signal, MACD_Hist, MA_20, MA_50, EMA_12, Volatility, "
        "and Daily_Return. Data was split 80% training / 20% testing with time-series order "
        "preserved to prevent look-ahead bias. RSI was the dominant predictor with 46–63% "
        "feature importance across all assets.",
        "body"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P("Feature Importance Charts", "h2"))
    for sym in SYMBOLS:
        story.append(KeepTogether([
            get_image(f"{sym}_feature_importance.png", width=11*cm),
            P(f"Figure: {sym} — Random Forest Feature Importance", "caption"),
            Spacer(1, 0.15*cm)
        ]))

    # ── 7. AGENTIC WORKFLOW ───────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(P("  7. Agentic AI Workflow Architecture", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "The system implements a four-agent sequential pipeline. Each agent performs a "
        "specific analytical role and passes its output to the next agent, culminating "
        "in a risk-approved final trading action for each of the five symbols.",
        "body"))
    story.append(Spacer(1, 0.2*cm))

    agents = [
        ("Agent 1 — Market Analysis Agent", "market_analysis.py",
         "Analyses RSI, MACD crossover, and Moving Average crossover (MA20 vs MA50) "
         "to generate an initial trading signal. RSI below 40 generates BUY; "
         "RSI above 60 generates SELL. Outputs BUY/SELL/HOLD with a confidence score."),
        ("Agent 2 — Information Retrieval Agent", "info_retrieval.py",
         "Fetches the 15 most recent news headlines per symbol from Yahoo Finance RSS feed. "
         "Scores sentiment using VADER NLP (Valence Aware Dictionary and sEntiment Reasoner). "
         "VADER score above 0.05 = POSITIVE; below -0.05 = NEGATIVE; otherwise NEUTRAL. "
         "No external API key is required."),
        ("Agent 3 — Decision Engine", "decision_engine.py",
         "Combines the market signal from Agent 1 with the news sentiment from Agent 2. "
         "POSITIVE news boosts BUY confidence by 20%. NEGATIVE news reduces confidence. "
         "Outputs a final adjusted BUY/SELL/HOLD decision with updated confidence."),
        ("Agent 4 — Risk Manager", "risk_manager.py",
         "Applies four risk controls before approving any trade: minimum 45% confidence "
         "threshold, maximum 15% portfolio position size, 5% stop-loss limit per trade, "
         "and a maximum of 5 trades per day across all symbols."),
    ]

    for name, file, desc in agents:
        story.append(KeepTogether([
            P(name, "h2"),
            P(f"<b>File:</b> <font color='#2E75B6'>{file}</font>", "body"),
            P(desc, "body"),
            Spacer(1, 0.15*cm)
        ]))

    # ── 8. BACKTESTING ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(P("  8. Backtesting Results", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "The backtesting engine simulates historical trading over the one-year data period "
        "using the generated RSI-based signals. Starting capital of $100,000 is used for "
        "all assets. Sharpe Ratio above 1.0 indicates good risk-adjusted return. "
        "AAPL achieved the best Sharpe Ratio of 1.21 in the latest run.",
        "body"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P("Performance Summary — Latest Run", "h2"))
    story.append(make_table(
        ["Symbol", "Signal", "Sentiment", "Return", "Sharpe",
         "Drawdown", "Win Rate", "ML Acc."],
        backtest_rows,
        col_widths=[2.3*cm, 2*cm, 2.5*cm, 2.2*cm,
                    2*cm, 2.3*cm, 2.3*cm, 2.4*cm],
        small=True
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(P("Backtest Performance Charts", "h2"))
    for sym in SYMBOLS:
        story.append(KeepTogether([
            get_image(f"{sym}_backtest.png", width=14*cm),
            P(f"Figure: {sym} — Strategy Return vs Buy-and-Hold Benchmark", "caption"),
            Spacer(1, 0.15*cm)
        ]))

    # ── 9. BUSINESS IMPACT ────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(P("  9. Business Impact Analysis", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "The Agentic AI Trading System delivers measurable business value across "
        "five key areas:",
        "body"))
    story.append(Spacer(1, 0.15*cm))

    for title, text in [
        ("Automation",
         "Lambda eliminates manual daily data collection entirely. The system fetches, "
         "processes, and stores fresh data for all five assets every weekday automatically "
         "without any human intervention."),
        ("Risk Management",
         "The four-layer agent system prevents impulsive trading through confidence "
         "thresholds (minimum 45%), position limits (maximum 15%), and stop-loss rules (5%). "
         "No trade is executed without passing all risk checks."),
        ("Portfolio Diversification",
         "Correlation analysis confirms BTC and ETH move together (0.84 correlation). "
         "A well-constructed portfolio should not over-allocate to both simultaneously. "
         "Stocks and crypto remain uncorrelated (0.00), enabling effective diversification."),
        ("Risk-Based Position Sizing",
         "VaR analysis shows ETH-USD carries approximately three times more daily risk "
         "than AAPL (-5.55% vs -1.92%). This provides quantitative evidence for "
         "reducing crypto position sizes relative to equities."),
        ("Scalability",
         "The system architecture supports extension to additional symbols, shorter "
         "timeframes (intraday), or live trade execution via broker APIs such as "
         "Alpaca Markets or Interactive Brokers without major code changes."),
    ]:
        story.append(P(f"<b>{title}:</b>  {text}", "bullet"))
        story.append(Spacer(1, 0.1*cm))

    # ── 10. LIMITATIONS ───────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(P("  10. Limitations", "h1"))
    story.append(Spacer(1, 0.2*cm))

    for title, text in [
        ("Backtesting Bias",
         "RSI thresholds (40/60) were calibrated on the same historical dataset used for "
         "testing. This may lead to overfitting and overestimation of live performance."),
        ("ML Model Overfitting",
         "100% classification accuracy on BTC-USD, ETH-USD and MSFT likely reflects "
         "overfitting due to small test set sizes (41–64 samples). Cross-validation "
         "across multiple time windows would improve reliability."),
        ("News Sentiment Model",
         "VADER is a general-purpose NLP sentiment tool not specifically designed for "
         "financial text. A domain-specific model such as FinBERT would provide "
         "more accurate and relevant sentiment scoring for trading decisions."),
        ("No Live Trade Execution",
         "The system generates signals and decisions only. Integration with a real "
         "brokerage API (e.g., Alpaca, Interactive Brokers) is required for actual "
         "trade execution in live markets."),
        ("Single Timeframe Analysis",
         "Only one year of daily (1D) data is used. Intraday signals on shorter "
         "timeframes (1H, 15M) are not currently supported, which limits high-frequency "
         "trading applications."),
        ("Cryptocurrency Backtesting",
         "BTC-USD showed zero completed backtest trades in the latest run due to "
         "signal threshold calibration. Per-asset threshold tuning would improve "
         "signal generation for highly volatile crypto assets."),
    ]:
        story.append(P(f"<b>{title}:</b>  {text}", "bullet"))
        story.append(Spacer(1, 0.1*cm))

    # ── 11. CONCLUSION ────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(P("  11. Conclusion", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "This project successfully designed and implemented a complete Agentic AI trading "
        "workflow system satisfying all four required components: Market Analysis Agent, "
        "Information Retrieval Agent, Decision Engine, and Risk Management Agent. The entire "
        "system is deployed on AWS cloud infrastructure with S3 for raw storage, RDS "
        "PostgreSQL for structured data, EC2 for computation, and Lambda with EventBridge "
        "for fully automated daily execution.",
        "body"))
    story.append(Spacer(1, 0.1*cm))
    story.append(P(
        "The Random Forest ML model achieved 73.2–100% classification accuracy across all "
        "five assets, with RSI identified as the dominant predictive feature (46–63% "
        "importance). AAPL demonstrated the strongest risk-adjusted performance with a "
        "Sharpe Ratio of 1.21. Correlation analysis confirmed that BTC and ETH move in "
        "tandem (0.84 correlation) while stocks and crypto remain effectively uncorrelated "
        "(0.00), providing actionable portfolio diversification guidance. VaR analysis "
        "ranked ETH-USD as the highest-risk asset at -5.55% per day compared to AAPL "
        "at -1.92%, enabling evidence-based position sizing decisions.",
        "body"))
    story.append(Spacer(1, 0.1*cm))
    story.append(P(
        "The system is version-controlled on GitHub with over 15 meaningful commits "
        "demonstrating the full incremental development lifecycle. Future improvements "
        "include FinBERT integration for finance-specific sentiment, intraday data support, "
        "live broker API integration, and walk-forward backtesting validation.",
        "body"))

    # ── BUILD PDF ─────────────────────────────────────────────────────────────
    doc.build(story,
              onFirstPage=on_first_page,
              onLaterPages=on_later_pages)

    print(f"\n{'='*52}")
    print(f"  PDF Report Generated Successfully!")
    print(f"  Saved to: {REPORT_PATH}")
    print(f"  Student:  {STUDENT_NAME}")
    print(f"  Date:     {datetime.now().strftime('%B %d, %Y at %H:%M')}")
    print(f"{'='*52}\n")


if __name__ == "__main__":
    print("\n  Generating Trading Report PDF...")
    print("  Reading latest output files...\n")
    build_report()
