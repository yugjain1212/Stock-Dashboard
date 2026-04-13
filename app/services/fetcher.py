import yfinance as yf
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database import SessionLocal, engine, Base
from app.models import StockPrice, Company
from app.services.processor import compute_metrics
import pandas as pd
import numpy as np
from datetime import datetime
import time


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
    "^NSEI": ("NIFTY 50", "Index", "Large Cap"),
}

BASE_PRICES = {
    "TCS.NS": 4200.0,
    "INFY.NS": 1800.0,
    "RELIANCE.NS": 2950.0,
    "HDFCBANK.NS": 1680.0,
    "WIPRO.NS": 580.0,
    "ICICIBANK.NS": 980.0,
    "BAJFINANCE.NS": 7200.0,
    "TATAMOTORS.NS": 980.0,
    "ADANIENT.NS": 2850.0,
    "^NSEI": 22500.0,
}


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified.")


def fetch_from_yfinance(symbol: str) -> pd.DataFrame:
    try:
        df = yf.download(symbol, period="1y", progress=False)
        if df.empty:
            return None
        df = df.reset_index()
        df.columns = ["date", "open", "high", "low", "close", "adj_close", "volume"]
        df = df.drop(columns=["adj_close"])
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df
    except Exception as e:
        print(f"yfinance error: {e}")
        return None


def generate_sample_data(symbol: str, base_price: float) -> pd.DataFrame:
    print(f"Generating sample data for {symbol}...")

    dates = pd.date_range(end=datetime.now(), periods=252, freq="B")
    dates = [d.date() for d in dates]

    np.random.seed(hash(symbol) % 2**32)
    returns = np.random.normal(0.0003, 0.012, len(dates))

    prices = [base_price]
    for i in range(1, len(dates)):
        prices.append(prices[-1] * (1 + returns[i]))

    data = []
    for i, d in enumerate(dates):
        close = prices[i]
        open_p = close * (1 + np.random.uniform(-0.008, 0.008))
        high_p = max(open_p, close) * (1 + abs(np.random.uniform(0, 0.01)))
        low_p = min(open_p, close) * (1 - abs(np.random.uniform(0, 0.01)))

        data.append(
            {
                "date": d,
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": close,
                "volume": int(np.random.uniform(500000, 5000000)),
            }
        )

    df = pd.DataFrame(data)
    return df


def fetch_symbol_data(symbol: str, db: Session) -> int:
    print(f"Fetching data for {symbol}...")

    df = fetch_from_yfinance(symbol)

    if df is None or df.empty:
        print(f"yfinance failed, generating sample data for {symbol}")
        df = generate_sample_data(symbol, BASE_PRICES.get(symbol, 1000.0))

    df = compute_metrics(df)

    inserted = 0
    for _, row in df.iterrows():
        existing = (
            db.query(StockPrice)
            .filter(and_(StockPrice.symbol == symbol, StockPrice.date == row["date"]))
            .first()
        )

        if existing:
            continue

        try:
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
        except Exception as e:
            print(f"Error adding row: {e}")
            continue

    db.commit()
    print(f"Inserted {inserted} new records for {symbol}")
    return inserted


def fetch_all_data():
    init_db()

    db = SessionLocal()
    try:
        for symbol, (name, sector, cap_category) in SYMBOLS.items():
            existing_company = (
                db.query(Company).filter(Company.symbol == symbol).first()
            )
            if not existing_company:
                company = Company(
                    symbol=symbol,
                    name=name,
                    sector=sector,
                    market_cap_category=cap_category,
                )
                db.add(company)
                print(f"Added company: {name} ({symbol})")

        db.commit()

        total_inserted = 0
        for symbol in SYMBOLS.keys():
            inserted = fetch_symbol_data(symbol, db)
            total_inserted += inserted
            time.sleep(0.3)

        print(f"\nTotal new records inserted: {total_inserted}")

    finally:
        db.close()


if __name__ == "__main__":
    fetch_all_data()
