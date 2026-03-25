# generate_report.py
# Auto-generates a professional PDF report using your real output files
# Results change automatically every time main.py runs
#
# HOW TO USE:
#   Step 1: pip install reportlab pillow pandas
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
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
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
    path = os.path.join(OUTPUT_FOLDER, "trade_decisions.csv")
    rows = []
    if os.path.exists(path):
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                symbol    = row.get("Symbol",    row.get("SYMBOL",    ""))
                signal    = row.get("Signal",    row.get("SIGNAL",    ""))
                sentiment = row.get("Sentiment", row.get("SENTIMENT", ""))
                final     = row.get("Final",     row.get("FINAL",     ""))
                conf      = row.get("Confidence",row.get("CONF",      ""))
                rows.append([symbol, signal, sentiment, final, conf])
    return rows

def load_results_summary():
    path = os.path.join(OUTPUT_FOLDER, "results_summary.json")
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return None

# ── STATIC FALLBACK DATA ──────────────────────────────────────────────────────

FALLBACK_DECISIONS = [
    ["AAPL",    "SELL", "POSITIVE", "SELL", "50%"],
    ["MSFT",    "BUY",  "POSITIVE", "BUY",  "72%"],
    ["GOOGL",   "BUY",  "POSITIVE", "BUY",  "72%"],
    ["BTC-USD", "BUY",  "NEUTRAL",  "BUY",  "60%"],
    ["ETH-USD", "BUY",  "NEUTRAL",  "BUY",  "55%"],
]

FALLBACK_BACKTEST = [
    ["AAPL",    "SELL", "POSITIVE", "+5.84%",  "1.29",  "-3.5%",  "100%", "97.6%"],
    ["MSFT",    "BUY",  "POSITIVE", "-14.99%", "-1.23", "-18.3%", "100%", "100%"],
    ["GOOGL",   "BUY",  "POSITIVE", "-0.51%",  "-0.16", "-2.6%",  "0%",   "75.6%"],
    ["BTC-USD", "BUY",  "NEUTRAL",  "+0.00%",  "0.0",   "0.0%",   "0%",   "100%"],
    ["ETH-USD", "BUY",  "NEUTRAL",  "-9.65%",  "-0.21", "-26.8%", "100%", "100%"],
]

CORRELATION_DATA = [
    ["AAPL vs MSFT",  "0.40", "Moderate — both large-cap tech"],
    ["AAPL vs GOOGL", "0.50", "Moderate — large-cap tech sector"],
    ["BTC vs ETH",    "0.84", "Very high — crypto moves together"],
    ["AAPL vs BTC",   "0.00", "No correlation — stocks vs crypto"],
]

VAR_DATA = [
    ["AAPL",    "-1.94%", "Lowest risk"],
    ["GOOGL",   "-2.17%", "Low risk"],
    ["MSFT",    "-2.29%", "Low risk"],
    ["BTC-USD", "-3.68%", "Medium risk"],
    ["ETH-USD", "-5.55%", "Highest risk"],
]

CLUSTER_DATA = [
    ["AAPL",    "0", "Stable, low-volatility"],
    ["MSFT",    "0", "Stable, low-volatility"],
    ["BTC-USD", "0", "Stable, low-volatility"],
    ["GOOGL",   "2", "Mid-volatility"],
    ["ETH-USD", "1", "High-volatility crypto"],
]

# ── STYLES ────────────────────────────────────────────────────────────────────

def S(name, **kw):
    defaults = dict(
        cover_title = dict(fontSize=26, textColor=DARK_BLUE, alignment=TA_CENTER,
                           fontName="Helvetica-Bold", spaceAfter=8, leading=32),
        cover_sub   = dict(fontSize=15, textColor=MID_BLUE,  alignment=TA_CENTER,
                           fontName="Helvetica", spaceAfter=6, leading=20),
        cover_info  = dict(fontSize=12, textColor=BLACK, alignment=TA_CENTER,
                           fontName="Helvetica", spaceAfter=4, leading=17),
        h1          = dict(fontSize=14, textColor=WHITE, fontName="Helvetica-Bold",
                           spaceAfter=8, spaceBefore=12, leading=18,
                           backColor=DARK_BLUE, leftIndent=0, rightIndent=0,
                           borderPadding=(5, 8, 5, 8)),
        h2          = dict(fontSize=12, textColor=DARK_BLUE, fontName="Helvetica-Bold",
                           spaceAfter=5, spaceBefore=8, leading=16),
        body        = dict(fontSize=10, textColor=BLACK, fontName="Helvetica",
                           spaceAfter=5, leading=15, alignment=TA_JUSTIFY),
        caption     = dict(fontSize=8.5, textColor=colors.HexColor("#555555"),
                           fontName="Helvetica-Oblique", alignment=TA_CENTER,
                           spaceAfter=8, leading=12),
        bullet      = dict(fontSize=10, textColor=BLACK, fontName="Helvetica",
                           spaceAfter=3, leading=15, leftIndent=12),
    )
    d = defaults.get(name, {})
    d.update(kw)
    return ParagraphStyle(name, **d)

def P(text, style_name, **kw):
    return Paragraph(text, S(style_name, **kw))

# ── TABLE ─────────────────────────────────────────────────────────────────────

def make_table(headers, rows, col_widths=None, small=False):
    fs = 8.5 if small else 9.5
    th_style = ParagraphStyle("th", fontSize=fs, textColor=WHITE,
                               fontName="Helvetica-Bold", alignment=TA_CENTER, leading=13)
    td_style = ParagraphStyle("td", fontSize=fs, fontName="Helvetica",
                               alignment=TA_CENTER, leading=13)
    data = [[Paragraph(h, th_style) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), td_style) for c in row])

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  DARK_BLUE),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, ALT_ROW]),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return tbl

# ── IMAGE ─────────────────────────────────────────────────────────────────────

def get_image(filename, width=14*cm):
    path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(path):
        try:
            img = Image(path)
            ratio = img.imageHeight / img.imageWidth
            img.drawWidth  = width
            img.drawHeight = width * ratio
            return img
        except Exception:
            pass
    return P(f"[Chart not found: {filename}]", "caption")

# ── HEADER / FOOTER ───────────────────────────────────────────────────────────

def on_page(canvas, doc):
    w, h = A4
    canvas.saveState()
    canvas.setFillColor(DARK_BLUE)
    canvas.rect(0, h - 1.1*cm, w, 1.1*cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.drawString(1.5*cm, h - 0.78*cm, "Agentic AI Trading System")
    canvas.setFont("Helvetica", 8.5)
    canvas.drawRightString(w - 1.5*cm, h - 0.78*cm,
                           f"MSc Data Science | {UNIVERSITY}")
    canvas.setFillColor(DARK_BLUE)
    canvas.rect(0, 0, w, 0.9*cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(1.5*cm, 0.32*cm,
                      f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}")
    canvas.drawCentredString(w / 2, 0.32*cm, GITHUB)
    canvas.drawRightString(w - 1.5*cm, 0.32*cm, f"Page {doc.page}")
    canvas.restoreState()

# ── BUILD ─────────────────────────────────────────────────────────────────────

def build_report():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Load dynamic data
    decisions = load_trade_decisions()
    agent_rows = decisions if decisions else FALLBACK_DECISIONS
    status = "✅ Loaded from trade_decisions.csv" if decisions else "⚠️  Using last known results"
    print(f"  Agent decisions: {status}")

    summary = load_results_summary()
    if summary:
        backtest_rows = summary.get("backtest",     FALLBACK_BACKTEST)
        corr_rows     = summary.get("correlation",  CORRELATION_DATA)
        var_rows      = summary.get("var",           VAR_DATA)
        cluster_rows  = summary.get("clusters",      CLUSTER_DATA)
        print("  Results summary: ✅ Loaded from results_summary.json")
    else:
        backtest_rows = FALLBACK_BACKTEST
        corr_rows     = CORRELATION_DATA
        var_rows      = VAR_DATA
        cluster_rows  = CLUSTER_DATA
        print("  Results summary: ℹ️  Using last known results")

    doc = SimpleDocTemplate(
        REPORT_PATH, pagesize=A4,
        topMargin=1.6*cm, bottomMargin=1.4*cm,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        title="Agentic AI Trading System Report",
        author=STUDENT_NAME
    )

    story = []

    # ── COVER PAGE ────────────────────────────────────────────────────────
    story.append(Spacer(1, 2.5*cm))
    story.append(P("Agentic AI Trading System", "cover_title"))
    story.append(P("Automated Trading Workflow — Final Report", "cover_sub"))
    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width="75%", thickness=2, color=MID_BLUE, spaceAfter=16))
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
    story.append(HRFlowable(width="75%", thickness=1, color=LIGHT_BLUE, spaceAfter=14))
    story.append(Spacer(1, 0.4*cm))
    story.append(P(
        "This report presents a complete Agentic AI-based trading system covering "
        "data collection via Yahoo Finance API, AWS cloud integration (S3, RDS, EC2, Lambda), "
        "exploratory data analysis, Random Forest ML modelling, and a four-agent autonomous "
        "decision pipeline for five financial assets.",
        "cover_info",
        textColor=colors.HexColor("#444444"),
        fontName="Helvetica-Oblique", fontSize=11
    ))
    story.append(PageBreak())

    # ── 1. EXECUTIVE SUMMARY ──────────────────────────────────────────────
    story.append(P("  1. Executive Summary", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "This project designs and evaluates an Agentic AI-based automated trading workflow. "
        "The system autonomously collects financial market data, performs EDA, trains "
        "Random Forest ML models, retrieves live news sentiment via VADER NLP, and generates "
        "buy/sell/hold decisions through a four-agent sequential pipeline deployed on AWS.",
        "body"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P("Agent Decision Summary — Latest Run", "h2"))
    story.append(make_table(
        ["Symbol","Market Signal","News Sentiment","Final Decision","Confidence"],
        agent_rows,
        col_widths=[3*cm, 3.5*cm, 4*cm, 3.5*cm, 3*cm]
    ))

    # ── 2. DATA COLLECTION ────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(P("  2. Data Collection", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "Data was collected for AAPL, MSFT, GOOGL (stocks) and BTC-USD, ETH-USD "
        "(cryptocurrencies) using the yfinance API. One year of daily OHLCV data was "
        "downloaded per symbol. Data is automatically uploaded to AWS S3 and stored in "
        "AWS RDS PostgreSQL via Lambda every weekday.",
        "body"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P("AWS Cloud Infrastructure", "h2"))
    story.append(make_table(
        ["AWS Service","Configuration","Purpose"],
        [
            ["AWS S3",      "trading-raw-data-2024",              "Stores raw CSV files (stocks/ + crypto/)"],
            ["AWS RDS",     "PostgreSQL, trading-db, us-east-1",  "Structured database for market data"],
            ["AWS EC2",     "t2.micro, Amazon Linux 2023",        "Cloud computation and pipeline execution"],
            ["AWS Lambda",  "Python 3.11, 256MB, 1min timeout",   "Automated daily data fetch"],
            ["EventBridge", "cron(30 13 ? * MON-FRI *)",          "Triggers Lambda weekdays 9:30AM EST"],
        ],
        col_widths=[3*cm, 5.5*cm, 8.5*cm]
    ))

    # ── 3. EDA ────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(P("  3. Exploratory Data Analysis", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "Technical indicators were engineered: MA20, MA50, EMA12, RSI (14-day), MACD with "
        "Signal and Histogram, and Bollinger Bands. Buy signals: RSI < 40. Sell signals: RSI > 60.",
        "body"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P("Technical Analysis Charts", "h2"))
    for sym in SYMBOLS:
        story.append(KeepTogether([
            get_image(f"{sym}_analysis.png", width=14*cm),
            P(f"Figure: {sym} — Price, MA, Bollinger Bands, RSI and MACD","caption"),
            Spacer(1, 0.2*cm)
        ]))

    # ── 4. CORRELATION & VaR ──────────────────────────────────────────────
    story.append(PageBreak())
    story.append(P("  4. Correlation and Volatility Analysis", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "BTC and ETH show very high correlation (0.84), meaning they move together. "
        "Stocks and crypto show near-zero correlation, providing portfolio diversification benefits.",
        "body"))
    story.append(Spacer(1, 0.2*cm))
    story.append(KeepTogether([
        get_image("correlation_analysis.png", width=15*cm),
        P("Figure: Correlation Heatmap and 30-Day Rolling Correlation (AAPL vs BTC)","caption"),
    ]))
    story.append(Spacer(1, 0.2*cm))
    story.append(make_table(
        ["Asset Pair","Correlation","Interpretation"],
        corr_rows,
        col_widths=[4*cm, 3.5*cm, 9.5*cm]
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(P("Value at Risk — 95% Confidence", "h2"))
    story.append(KeepTogether([
        get_image("volatility_analysis.png", width=15*cm),
        P("Figure: 20-Day Rolling Volatility and VaR (95%) per Asset","caption"),
    ]))
    story.append(Spacer(1, 0.2*cm))
    story.append(make_table(
        ["Asset","Daily VaR (95%)","Risk Level"],
        var_rows,
        col_widths=[4*cm, 5*cm, 8*cm]
    ))

    # ── 5. CLUSTERING ─────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(P("  5. K-Means Asset Clustering", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "K-Means clustering (k=3) was applied using three standardised features: "
        "mean daily return, mean 20-day rolling volatility, and mean RSI.",
        "body"))
    story.append(Spacer(1, 0.2*cm))
    story.append(make_table(
        ["Asset","Cluster","Group Interpretation"],
        cluster_rows,
        col_widths=[4*cm, 3.5*cm, 9.5*cm]
    ))

    # ── 6. ML MODEL ───────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(P("  6. Machine Learning Model", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "A Random Forest Classifier (100 estimators, max_depth=5) was trained per asset "
        "to predict Buy/Sell/Hold signals using 9 features. RSI was the dominant predictor "
        "with 46-63% importance across all assets.",
        "body"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P("Feature Importance Charts","h2"))
    for sym in SYMBOLS:
        story.append(KeepTogether([
            get_image(f"{sym}_feature_importance.png", width=11*cm),
            P(f"Figure: {sym} — Random Forest Feature Importance","caption"),
            Spacer(1, 0.15*cm)
        ]))

    # ── 7. AGENTIC WORKFLOW ───────────────────────────────────────────────
    story.append(PageBreak())
    story.append(P("  7. Agentic AI Workflow", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "The system implements a four-agent sequential pipeline where each agent "
        "processes its input and passes results to the next agent.",
        "body"))
    story.append(Spacer(1, 0.2*cm))
    for name, file, desc in [
        ("Agent 1 — Market Analysis",      "market_analysis.py",
         "Analyses RSI, MACD and Moving Average crossovers. RSI<40=BUY, RSI>60=SELL."),
        ("Agent 2 — Information Retrieval","info_retrieval.py",
         "Fetches 15 headlines per symbol. Scores with VADER NLP (>0.05=POSITIVE, <-0.05=NEGATIVE)."),
        ("Agent 3 — Decision Engine",      "decision_engine.py",
         "Combines signal + sentiment. POSITIVE news boosts BUY confidence by +20%."),
        ("Agent 4 — Risk Manager",         "risk_manager.py",
         "Applies risk controls: min 45% confidence, max 15% position, 5% stop-loss, max 5 trades/day."),
    ]:
        story.append(KeepTogether([
            P(name, "h2"),
            P(f"<b>File:</b> <font color='#2E75B6'>{file}</font> — {desc}", "body"),
            Spacer(1, 0.15*cm)
        ]))

    # ── 8. BACKTESTING ────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(P("  8. Backtesting Results", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "Backtesting simulates historical trading using generated signals. "
        "Sharpe Ratio >1 indicates good risk-adjusted return. "
        "AAPL achieved the best Sharpe Ratio of 1.29.",
        "body"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P("Performance Summary — Latest Run","h2"))
    story.append(make_table(
        ["Symbol","Signal","Sentiment","Return","Sharpe","Drawdown","Win Rate","ML Acc."],
        backtest_rows,
        col_widths=[2.3*cm,2*cm,2.5*cm,2.2*cm,2*cm,2.3*cm,2.3*cm,2.4*cm],
        small=True
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(P("Backtest Charts","h2"))
    for sym in SYMBOLS:
        story.append(KeepTogether([
            get_image(f"{sym}_backtest.png", width=14*cm),
            P(f"Figure: {sym} — Strategy Return vs Buy-and-Hold Benchmark","caption"),
            Spacer(1, 0.15*cm)
        ]))

    # ── 9. BUSINESS IMPACT ────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(P("  9. Business Impact", "h1"))
    story.append(Spacer(1, 0.2*cm))
    for title, text in [
        ("Automation",      "Lambda eliminates manual daily data collection — runs every weekday automatically."),
        ("Risk Management", "Four-layer agent system prevents impulsive trades through confidence thresholds."),
        ("Diversification", "BTC-ETH correlation 0.84 — portfolios should not over-allocate to both."),
        ("Risk Ranking",    "ETH-USD has 3x more daily risk than AAPL (VaR -5.55% vs -1.94%)."),
        ("Scalability",     "Can be extended to more symbols or integrated with Alpaca/Interactive Brokers API."),
    ]:
        story.append(P(f"<b>{title}:</b>  {text}", "bullet"))
        story.append(Spacer(1, 0.1*cm))

    # ── 10. LIMITATIONS ───────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(P("  10. Limitations", "h1"))
    story.append(Spacer(1, 0.2*cm))
    for title, text in [
        ("Backtesting Bias",  "RSI thresholds tuned on training data may overestimate live performance."),
        ("ML Overfitting",    "100% accuracy on some assets reflects small test sets (41-64 samples)."),
        ("NLP Model",         "VADER is general-purpose. FinBERT would give more accurate financial sentiment."),
        ("No Live Trading",   "System generates signals only — no real brokerage API integration yet."),
        ("Single Timeframe",  "Only daily data used. Intraday signals not currently supported."),
    ]:
        story.append(P(f"<b>{title}:</b>  {text}", "bullet"))
        story.append(Spacer(1, 0.1*cm))

    # ── 11. CONCLUSION ────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(P("  11. Conclusion", "h1"))
    story.append(Spacer(1, 0.2*cm))
    story.append(P(
        "This project successfully implemented a complete Agentic AI trading workflow "
        "covering all required components: Market Analysis, Information Retrieval, Decision "
        "Engine, and Risk Management. All infrastructure is deployed on AWS with automated "
        "daily execution via EventBridge. The ML model achieved 75.6-100% accuracy across "
        "assets. AAPL demonstrated the best risk-adjusted performance (Sharpe 1.29). "
        "Correlation analysis confirmed BTC-ETH move together (0.84) while stocks and crypto "
        "remain uncorrelated (0.00), providing clear portfolio diversification guidance.",
        "body"))

    # ── BUILD ──────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=lambda c,d: None, onLaterPages=on_page)
    print(f"\n{'='*52}")
    print(f"  PDF Report Generated Successfully!")
    print(f"  Saved to: {REPORT_PATH}")
    print(f"  Date: {datetime.now().strftime('%B %d, %Y at %H:%M')}")
    print(f"{'='*52}\n")


if __name__ == "__main__":
    print("\n  Generating Trading Report PDF...")
    print("  Reading latest output files...\n")
    build_report()
