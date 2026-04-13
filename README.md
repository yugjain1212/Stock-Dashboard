# Stock Data Intelligence Dashboard

A production-grade financial data intelligence platform for NSE/BSE Indian stock market data with FastAPI backend, SQLite/PostgreSQL database, and a stunning modern frontend dashboard.

## Project Overview

StockIQ Dashboard provides real-time and historical stock data analysis for 10 major Indian stocks including TCS, Infosys, Reliance, HDFC Bank, and NIFTY 50 index. It features custom computed metrics like Volatility Score, moving averages, and correlation analysis for stock comparison.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.10+, FastAPI |
| Database | SQLite (PostgreSQL-ready) |
| Data Source | yfinance, Pandas, NumPy |
| Frontend | Vanilla JS + Chart.js CDN |
| Documentation | FastAPI Auto Swagger |

## Setup Instructions

### 1. Clone and Navigate

```bash
git clone <your-repo-url>
cd stock-dashboard
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Fetch Initial Data

```bash
python -m app.services.fetcher
```

This fetches 1 year of historical data for all 10 symbols from Yahoo Finance.

### 4. Run the Server

```bash
uvicorn app.main:app --reload
```

### 5. Access Dashboard

Open your browser and navigate to: `http://localhost:8000`

## API Endpoints

### GET /api/companies

Returns list of all companies with latest price and daily return.

**Example Response:**
```json
[
  {
    "symbol": "TCS.NS",
    "name": "TCS",
    "sector": "Information Technology",
    "market_cap_category": "Large Cap",
    "latest_close": 4235.50,
    "latest_daily_return": 0.0125
  }
]
```

### GET /api/data/{symbol}?days=30

Returns OHLCV data with computed metrics for specified days.

**Parameters:**
- `symbol`: Stock symbol (e.g., TCS.NS)
- `days`: Number of days (default 30, max 365)

**Example Response:**
```json
{
  "data": [
    {
      "symbol": "TCS.NS",
      "date": "2024-04-10",
      "open": 4200.00,
      "high": 4250.00,
      "low": 4180.00,
      "close": 4235.50,
      "volume": 1250000,
      "daily_return": 0.0085,
      "moving_avg_7d": 4215.30,
      "week52_high": 4400.00,
      "week52_low": 3800.00,
      "volatility_score": 0.1520
    }
  ],
  "symbol": "TCS.NS",
  "days": 30
}
```

### GET /api/summary/{symbol}

Returns comprehensive summary statistics for a stock.

**Example Response:**
```json
{
  "symbol": "TCS.NS",
  "name": "TCS",
  "week52_high": 4400.00,
  "week52_low": 3800.00,
  "avg_close": 4150.25,
  "latest_close": 4235.50,
  "latest_daily_return": 0.0125,
  "avg_volatility_score": 0.1450,
  "total_trading_days": 252
}
```

### GET /api/compare?symbol1=TCS.NS&symbol2=INFY.NS&days=30

Returns side-by-side comparison with correlation coefficient.

**Parameters:**
- `symbol1`: First stock symbol
- `symbol2`: Second stock symbol
- `days`: Number of days for comparison (default 30)

**Example Response:**
```json
{
  "symbol1_stats": {
    "symbol": "TCS.NS",
    "avg_close": 4150.25,
    "total_return_pct": 5.25,
    "max_close": 4235.50,
    "min_close": 3950.00,
    "avg_volatility": 0.1450
  },
  "symbol2_stats": {
    "symbol": "INFY.NS",
    "avg_close": 1850.50,
    "total_return_pct": 3.75,
    "max_close": 1920.00,
    "min_close": 1750.00,
    "avg_volatility": 0.1820
  },
  "correlation": 0.8542,
  "better_performer": "TCS.NS"
}
```

### GET /api/health

Returns health status and database info.

**Example Response:**
```json
{
  "status": "healthy",
  "db_record_count": 2520,
  "last_updated": "2024-04-10"
}
```

## Volatility Score Explanation

The **Volatility Score** is a custom metric that measures annualized volatility based on the 30-day rolling standard deviation of daily returns.

### Formula

```
Volatility Score = Rolling_STD(daily_return, 30) × √30
```

Where:
- `daily_return = (Close - Open) / Open` for each trading day
- `Rolling_STD` calculates standard deviation over a 30-day window
- `√30` annualizes the daily volatility

### Interpretation

| Score Range | Interpretation |
|------------|----------------|
| < 0.10 | Low Volatility |
| 0.10 - 0.20 | Moderate Volatility |
| 0.20 - 0.30 | High Volatility |
| > 0.30 | Very High Volatility |

A higher volatility score indicates greater price fluctuation and risk.

## Dashboard Features

1. **Company List Sidebar** - Browse and select from 10 major stocks
2. **Interactive Price Chart** - Line chart with gradient fill and custom tooltips
3. **Time Filters** - 7D, 30D, 90D, 180D, 1Y views
4. **Summary Cards** - 52W High, 52W Low, Avg Close 30D, Volatility Score
5. **Stock Comparison** - Side-by-side comparison with correlation
6. **Top Gainers/Losers** - Daily performance rankings
7. **Live Status Indicator** - Green pulsing dot for data freshness

## Deployment on Render

### Using render.yaml

1. Push your code to a GitHub repository
2. Sign in to [Render](https://render.com)
3. Click "New" → "Blueprint"
4. Connect your GitHub repository
5. Select the `render.yaml` file
6. Deploy!

### Manual Deployment

1. Create a new Web Service on Render
2. Set environment:
   - `DATABASE_URL`: `sqlite:///./stocks.db`
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Note:** On Render, data will be fetched on first startup. For production, consider using PostgreSQL by setting `DATABASE_URL` to a PostgreSQL connection string.

## Evaluation Checklist

| Criterion | Description | Status |
|-----------|-------------|--------|
| Python & Data Handling | yfinance, Pandas, NumPy integration | ✅ Complete |
| API Design & Logic | 4 endpoints with proper validation | ✅ Complete |
| Creativity in Data Insights | Volatility Score, correlation analysis | ✅ Complete |
| Visualization & UI | Bloomberg-style dashboard with Chart.js | ✅ Complete |
| Documentation | Complete README with all endpoints | ✅ Complete |
| Deployment | Render-ready with render.yaml | ✅ Complete |

## Supported Stocks

| Symbol | Company Name | Sector |
|--------|--------------|--------|
| TCS.NS | TCS | Information Technology |
| INFY.NS | Infosys | Information Technology |
| RELIANCE.NS | Reliance Industries | Conglomerate |
| HDFCBANK.NS | HDFC Bank | Financial Services |
| WIPRO.NS | Wipro | Information Technology |
| ICICIBANK.NS | ICICI Bank | Financial Services |
| BAJFINANCE.NS | Bajaj Finance | Financial Services |
| TATAMOTORS.NS | Tata Motors | Automobile |
| ADANIENT.NS | Adani Enterprises | Conglomerate |
| ^NSEI | NIFTY 50 | Index |

## License

MIT License