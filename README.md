# 🤖 Agentic AI Trading System

**MSc Data Science | Coventry University**  
**Student:** Ahamed Rikaz  
**Module:** Agentic AI Workflow for Automated Trading (Finance Domain)

---

## 📌 Project Overview

An autonomous multi-agent AI trading system that collects financial market data, performs exploratory data analysis, trains machine learning models, retrieves live news sentiment, and generates buy/sell/hold trading decisions — all running on AWS cloud infrastructure.

The system covers **3 stocks** (AAPL, MSFT, GOOGL) and **2 cryptocurrencies** (BTC-USD, ETH-USD).

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   AWS CLOUD INFRASTRUCTURE               │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │  AWS S3  │    │ AWS RDS  │    │     AWS EC2      │  │
│  │  (Raw    │    │(PostgreSQL    │  (Computation /  │  │
│  │  Data)   │    │  DB)     │    │   Pipeline Run)  │  │
│  └──────────┘    └──────────┘    └──────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  AWS Lambda (Automated Daily Fetch - 9:30AM EST) │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│                   DATA PIPELINE (main.py)                │
│                                                         │
│  Phase 1        Phase 2        Phase 3        Phase 4   │
│  ─────────      ─────────      ─────────      ───────── │
│  Data           EDA &          Agentic        Back-      │
│  Collection  →  Feature    →   AI Agents  →   testing   │
│  (yfinance)     Engineering    (4 agents)      Results  │
└─────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│               4-AGENT DECISION WORKFLOW                  │
│                                                         │
│  Agent 1           Agent 2           Agent 3            │
│  ──────────        ──────────        ──────────         │
│  Market         →  Info          →   Decision           │
│  Analysis          Retrieval         Engine             │
│  (RSI/MACD)        (VADER NLP        (Combined          │
│                    Sentiment)         Signal)           │
│                                          │              │
│                                          ▼              │
│                                      Agent 4            │
│                                      ──────────         │
│                                      Risk               │
│                                      Manager            │
│                                      (Final Action)     │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
agentic-trading-system/
│
├── ingestion/
│   └── fetch_data.py          # Phase 1: Downloads data → S3 + RDS
│
├── eda/
│   └── analysis.py            # Phase 2: EDA, ML model, charts
│
├── agents/
│   ├── market_analysis.py     # Agent 1: RSI/MACD/MA signals
│   ├── info_retrieval.py      # Agent 2: VADER NLP news sentiment
│   ├── decision_engine.py     # Agent 3: Combines signal + sentiment
│   ├── risk_manager.py        # Agent 4: Risk checks + final action
│   └── orchestrator.py        # Runs all 4 agents per symbol
│
├── output/
│   ├── backtest.py            # Sharpe Ratio, Drawdown, Win Rate
│   ├── *_analysis.png         # Technical analysis charts
│   ├── *_backtest.png         # Backtest performance charts
│   ├── *_feature_importance.png  # ML feature importance charts
│   ├── correlation_analysis.png  # Asset correlation heatmap
│   ├── volatility_analysis.png   # Rolling volatility + VaR
│   └── trade_decisions.csv    # All agent decisions log
│
├── lambda_function.py         # AWS Lambda: automated daily fetch
├── main.py                    # Master runner: all 5 phases
├── requirements.txt           # Python dependencies
└── .env                       # AWS credentials (NOT in GitHub)
```

---

## ☁️ AWS Cloud Infrastructure

| Service | Configuration | Purpose |
|---------|--------------|---------|
| **AWS S3** | Bucket: `trading-raw-data-2024` | Stores raw CSV data (stocks/ + crypto/ folders) |
| **AWS RDS** | PostgreSQL, `trading-db`, us-east-1 | Structured database storage |
| **AWS EC2** | `t2.micro`, Amazon Linux 2023 | Cloud computation server |
| **AWS Lambda** | Python 3.11, 256MB, 1min timeout | Automated daily data fetch |
| **EventBridge** | `cron(30 13 ? * MON-FRI *)` | Triggers Lambda every weekday 9:30 AM EST |

---

## 🤖 Agentic AI Workflow

### Agent 1 — Market Analysis Agent (`market_analysis.py`)
Analyses technical indicators to generate trading signals:
- **RSI** (Relative Strength Index): RSI < 40 = BUY signal, RSI > 60 = SELL signal
- **MACD** crossover detection
- **Moving Average** crossover (MA20 vs MA50)
- Outputs: BUY / SELL / HOLD with confidence score

### Agent 2 — Information Retrieval Agent (`info_retrieval.py`)
Retrieves and analyses live news using VADER NLP:
- Fetches 15 latest headlines per symbol from Yahoo Finance RSS
- Scores sentiment using **VADER** (Valence Aware Dictionary and sEntiment Reasoner)
- VADER score > 0.05 = POSITIVE, < -0.05 = NEGATIVE, else NEUTRAL
- No API key required — works offline

### Agent 3 — Decision Engine (`decision_engine.py`)
Combines market signal + news sentiment → adjusted final decision:
- POSITIVE news + BUY signal → confidence boosted (+20%)
- NEGATIVE news + BUY signal → confidence reduced
- Outputs: final BUY / SELL / HOLD with adjusted confidence

### Agent 4 — Risk Manager (`risk_manager.py`)
Applies risk controls before approving any trade:
- Minimum confidence threshold: **45%**
- Maximum position size: **15%** of portfolio
- Stop-loss limit: **5%**
- Maximum trades per day: **5**

---

## 📊 Final Results

### Agent Decision Summary

| Symbol | Signal | Sentiment (VADER) | Final Decision | Confidence |
|--------|--------|-------------------|----------------|------------|
| AAPL | SELL | POSITIVE (+0.108) | SELL | 50% |
| MSFT | BUY | POSITIVE (+0.167) | BUY | 72% |
| GOOGL | BUY | POSITIVE (+0.228) | BUY | 72% |
| BTC-USD | BUY | NEUTRAL (+0.012) | BUY | 60% |
| ETH-USD | BUY | NEUTRAL (+0.024) | BUY | 55% |

### Backtesting Performance

| Symbol | Return | Sharpe Ratio | Max Drawdown | Win Rate | ML Accuracy |
|--------|--------|-------------|--------------|----------|-------------|
| AAPL | +5.84% | 1.29 ✅ | -3.5% | 100% | 97.6% |
| MSFT | -14.99% | -1.23 | -18.3% | 100% | 100% |
| GOOGL | -0.51% | -0.16 | -2.6% | 0% | 75.6% |
| BTC-USD | +0.00% | 0.0 | 0.0% | 0% | 100% |
| ETH-USD | -9.65% | -0.21 | -26.8% | 100% | 100% |

> AAPL achieved a Sharpe Ratio of 1.29 (>1 = good risk-adjusted return)

### Correlation Analysis

| Asset Pair | Correlation | Interpretation |
|-----------|-------------|----------------|
| AAPL ↔ MSFT | 0.40 | Moderate (both large-cap tech) |
| AAPL ↔ GOOGL | 0.50 | Moderate (large-cap tech) |
| BTC ↔ ETH | 0.84 | Very high (crypto moves together) |
| AAPL ↔ BTC | 0.00 | No correlation (stocks vs crypto) |

### Value at Risk (95% confidence, daily)

| Asset | VaR | Risk Level |
|-------|-----|------------|
| AAPL | -1.94% | 🟢 Lowest risk |
| GOOGL | -2.17% | 🟡 Low risk |
| MSFT | -2.29% | 🟡 Low risk |
| BTC-USD | -3.68% | 🟠 Medium risk |
| ETH-USD | -5.55% | 🔴 Highest risk |

### K-Means Asset Clustering

| Asset | Cluster | Group |
|-------|---------|-------|
| AAPL | 0 | Stable low-volatility |
| MSFT | 0 | Stable low-volatility |
| BTC-USD | 0 | Stable low-volatility |
| GOOGL | 2 | Mid-volatility |
| ETH-USD | 1 | High-volatility crypto |

---

## 🧠 Machine Learning Model

**Algorithm:** Random Forest Classifier  
**Features:** RSI, MACD, MACD_Signal, MACD_Hist, MA_20, MA_50, EMA_12, Volatility, Daily_Return  
**Target:** BUY / SELL / HOLD signals  
**Split:** 80% training / 20% testing (time-series order preserved)

**Top Feature Importances (across all assets):**
- RSI: ~55% importance (most predictive)
- MACD: ~18% importance
- MACD_Histogram: ~11% importance

---

## 🚀 How to Run

### Prerequisites
```bash
pip install -r requirements.txt
```

### Environment Setup
Create a `.env` file in the root folder:
```
AWS_ACCESS_KEY_ID=YOUR_KEY_HERE
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_HERE
AWS_REGION=us-east-1
S3_BUCKET_NAME=trading-raw-data-2024
RDS_ENDPOINT=YOUR_RDS_ENDPOINT
RDS_USER=postgres
RDS_PASSWORD=YOUR_PASSWORD
RDS_DB=trading_db
```

### Run Full Pipeline
```bash
python main.py
```

This runs all 5 phases:
1. Data collection → S3 + RDS
2. EDA + ML model training
3. 4-agent decision workflow
4. Backtesting with Sharpe Ratio
5. Cross-asset correlation + VaR analysis

### Run on EC2 (Cloud)
```bash
ssh -i trading-key.pem ec2-user@54.147.39.3
cd agentic-trading-system
python main.py
```

---

## 📦 Dependencies

```
yfinance==0.2.x        # Market data API
pandas                 # Data manipulation
numpy                  # Numerical computing
matplotlib             # Charts and visualizations
seaborn                # Statistical visualizations
scikit-learn           # Random Forest ML model
ta                     # Technical indicators (RSI, MACD, BB)
boto3                  # AWS SDK (S3, Lambda)
psycopg2-binary        # PostgreSQL connection
python-dotenv          # Environment variables
sqlalchemy             # Database ORM
feedparser             # RSS news feed parsing
vaderSentiment         # NLP sentiment analysis
```

---

## ⚠️ Limitations

1. **Backtesting bias** — RSI thresholds (40/60) were tuned on the same data used for testing, which may overestimate performance
2. **ML accuracy** — 100% accuracy on BTC/ETH/MSFT likely indicates overfitting due to limited test data (41-64 samples)
3. **News sentiment** — VADER is a general-purpose NLP tool; a finance-specific model (e.g. FinBERT) would improve accuracy
4. **No live trading** — System generates signals only; no real brokerage API integration
5. **Single timeframe** — Only 1-year daily data; intraday signals are not supported
6. **Crypto gaps** — BTC-USD backtest showed 0 trades due to signal threshold calibration

---

## 💼 Business Impact

- **Automation:** Lambda eliminates manual daily data collection — runs every weekday at 9:30 AM EST automatically
- **Risk management:** 4-layer agent system prevents impulsive trades through confidence thresholds and position limits
- **Diversification insight:** Correlation analysis shows BTC/ETH move together (0.84) — portfolio should not over-allocate to both
- **Risk ranking:** ETH-USD has 3x more daily risk than AAPL (VaR -5.55% vs -1.94%) — useful for portfolio sizing
- **Scalability:** System can be extended to more symbols, timeframes, or integrated with real broker APIs (e.g. Alpaca, Interactive Brokers)

---

## 📜 Git Commit History

The project was built incrementally with meaningful commits demonstrating development progress:

- `feat: project structure created`
- `feat: data collection with S3 and RDS upload`
- `feat: EDA with ML model, correlation, volatility analysis`
- `feat: market analysis agent`
- `feat: VADER NLP news sentiment agent`
- `feat: decision engine with sentiment integration`
- `feat: risk management agent`
- `feat: orchestrator connects all 4 agents`
- `feat: enhanced backtesting with Sharpe, drawdown, win rate`
- `feat: AWS Lambda handler for automated daily data fetch`
- `feat: complete main pipeline with ML and cross-asset analysis`
- `fix: adjusted RSI thresholds to 40/60 for buy/sell signals`
- `fix: correlation chart order and FutureWarning`
- `feat: complete agentic trading system - MSc submission ready`

---

*MSc Data Science | Coventry University | Agentic AI Trading System*
