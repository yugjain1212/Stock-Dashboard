import requests
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database import SessionLocal, engine, Base
from app.models import StockPrice, Company
from app.services.processor import compute_metrics
import numpy as np
from datetime import datetime, timedelta
import time


# NSE India stock symbols (with .NS for compatibility)
SYMBOLS = {
    "TCS.NS": ("TCS", "Information Technology", "Large Cap"),
    "INFY.NS": ("Infosys", "Information Technology", "Large Cap"),
    "RELIANCE.NS": ("Reliance Industries", "Conglomerate", "Large Cap"),
    "HDFCBANK.NS": ("HDFC Bank", "Financial Services", "Large Cap"),
    "WIPRO.NS": ("Wipro", "Information Technology", "Large Cap"),
    "ICICIBANK.NS": ("ICICI Bank", "Financial Services", "Large Cap"),
    "BAJFINANCE.NS": ("Bajaj Finance", "Financial Services", "Large Cap"),
    "TATAMOTORS.NS": ("Tata Motors", "Automobile", "Large Cap"),
    "ADANIENT.NS": ("Adani Enterprises", "Conglomerate", "Mid Cap"),
}

# NSE India API for live quotes
BASE_URL = "https://www.nseindia.com/api"


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified.")


def get_nse_quote(symbol: str) -> dict:
    """Fetch live quote from NSE India"""
    # Remove .NS suffix for API call
    nse_symbol = symbol.replace(".NS", "")
    try:
        session = requests.Session()
        session.get(
            "https://www.nseindia.com",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )

        url = f"{BASE_URL}/quote-equity?symbol={nse_symbol}"
        response = session.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            },
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            info = data.get("info", {})
            priceInfo = data.get("priceInfo", {})

            return {
                "symbol": symbol,
                "name": info.get("companyName", symbol),
                "open": float(priceInfo.get("open", 0)),
                "high": float(priceInfo.get("intraDayHigh", 0)),
                "low": float(priceInfo.get("intraDayLow", 0)),
                "close": float(priceInfo.get("lastPrice", 0)),
                "volume": int(priceInfo.get("total traded volume", 0)),
                "previous_close": float(priceInfo.get("previousClose", 0)),
                "day_change": float(priceInfo.get("change", 0)),
                "day_change_pct": float(priceInfo.get("pchange", 0)),
            }
    except Exception as e:
        print(f"NSE API error for {symbol}: {e}")
        return None


def get_historical_data(symbol: str) -> list:
    """Get historical data from NSE"""
    # Remove .NS suffix for API call
    nse_symbol = symbol.replace(".NS", "")
    try:
        session = requests.Session()
        session.get(
            "https://www.nseindia.com",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )

        # Get last 30 days historical data
        url = f"{BASE_URL}/historical-equitySymbols?symbol={nse_symbol}&fromdate=01-01-2025&todate=13-04-2026"
        response = session.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            },
            timeout=15,
        )

        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                records = []
                for day in data["data"]:
                    records.append(
                        {
                            "date": day.get("CH_TIMESTAMP", datetime.now().date()),
                            "open": float(day.get("CH_OPENING_PRICE", 0)),
                            "high": float(day.get("CH_INTRADAY_HIGH", 0)),
                            "low": float(day.get("CH_INTRADAY_LOW", 0)),
                            "close": float(day.get("CH_CLOSING_PRICE", 0)),
                            "volume": int(day.get("CH_TOT_TRADED_QTY", 0)),
                        }
                    )
                return records
    except Exception as e:
        print(f"Historical data error for {symbol}: {e}")
    return None


def generate_sample_data(symbol: str) -> list:
    """Generate realistic sample data when API fails"""
    print(f"Generating sample data for {symbol}...")

    dates = [(datetime.now() - timedelta(days=i)).date() for i in range(251, -1, -1)]

    np.random.seed(hash(symbol) % 2**32)
    base_price = 1000 + (hash(symbol) % 1000)
    returns = np.random.normal(0.0003, 0.015, len(dates))

    prices = [base_price]
    for i in range(1, len(dates)):
        prices.append(prices[-1] * (1 + returns[i]))

    data = []
    for i, d in enumerate(dates):
        close = prices[i]
        open_p = close * (1 + np.random.uniform(-0.005, 0.005))
        high_p = max(open_p, close) * (1 + abs(np.random.uniform(0, 0.01)))
        low_p = min(open_p, close) * (1 - abs(np.random.uniform(0, 0.01)))

        data.append(
            {
                "date": d,
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": close,
                "volume": int(np.random.uniform(100000, 2000000)),
            }
        )

    return data


def fetch_live_quotes(db: Session) -> int:
    """Fetch live quotes for all stocks"""
    inserted = 0

    for symbol, (name, sector, cap_category) in SYMBOLS.items():
        # Check if company exists
        existing = db.query(Company).filter(Company.symbol == symbol).first()
        if not existing:
            company = Company(
                symbol=symbol,
                name=name,
                sector=sector,
                market_cap_category=cap_category,
            )
            db.add(company)
            print(f"Added company: {name}")

        # Get live quote
        quote = get_nse_quote(symbol)

        if quote:
            # Store today's data
            today = datetime.now().date()
            existing = (
                db.query(StockPrice)
                .filter(and_(StockPrice.symbol == symbol, StockPrice.date == today))
                .first()
            )

            if not existing:
                daily_return = (
                    (quote["close"] - quote["open"]) / quote["open"]
                    if quote["open"] > 0
                    else 0
                )

                price = StockPrice(
                    symbol=symbol,
                    date=today,
                    open=quote["open"],
                    high=quote["high"],
                    low=quote["low"],
                    close=quote["close"],
                    volume=quote["volume"],
                    daily_return=daily_return,
                )
                db.add(price)
                inserted += 1
                print(f"{symbol}: ₹{quote['close']} ({quote['day_change_pct']:+.2f}%)")
            else:
                print(f"{symbol}: Already up to date")
        else:
            print(f"Failed to get live data for {symbol}")

        time.sleep(1)

    db.commit()
    return inserted


def fetch_historical_data(db: Session) -> int:
    """Fetch historical data for all stocks"""
    inserted = 0

    for symbol in SYMBOLS.keys():
        data = get_historical_data(symbol)

        if data is None or len(data) == 0:
            print(f"No historical data for {symbol}, using sample")
            data = generate_sample_data(symbol)
        else:
            print(f"Got {len(data)} days for {symbol}")

        data = compute_metrics(data)

        for row in data:
            existing = (
                db.query(StockPrice)
                .filter(
                    and_(StockPrice.symbol == symbol, StockPrice.date == row["date"])
                )
                .first()
            )

            if not existing:
                price = StockPrice(
                    symbol=symbol,
                    date=row["date"],
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=int(row["volume"]),
                    daily_return=row["daily_return"],
                    moving_avg_7d=row["moving_avg_7d"],
                    week52_high=row["week52_high"],
                    week52_low=row["week52_low"],
                    volatility_score=row["volatility_score"],
                )
                db.add(price)
                inserted += 1

        time.sleep(0.5)

    db.commit()
    return inserted


def fetch_all_data():
    """Main function to fetch all data"""
    init_db()

    db = SessionLocal()
    try:
        # First try to get live quotes
        print("\n=== Fetching Live NSE Data ===")
        live_count = fetch_live_quotes(db)
        print(f"Inserted {live_count} live records")

        # Then get historical data for charts
        print("\n=== Fetching Historical Data ===")
        hist_count = fetch_historical_data(db)
        print(f"Inserted {hist_count} historical records")

    finally:
        db.close()


if __name__ == "__main__":
    fetch_all_data()
