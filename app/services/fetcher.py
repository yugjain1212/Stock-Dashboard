import yfinance as yf
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database import SessionLocal, engine, Base
from app.models import StockPrice, Company
from app.services.processor import compute_metrics
import pandas as pd
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


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified.")


def fetch_symbol_data(symbol: str, db: Session) -> int:
    print(f"Fetching data for {symbol}...")

    try:
        df = yf.download(symbol, period="1y", progress=False)

        if df.empty:
            print(f"No data returned for {symbol}")
            return 0

        df = df.reset_index()
        df.columns = ["date", "open", "high", "low", "close", "adj_close", "volume"]
        df = df.drop(columns=["adj_close"])
        df["date"] = pd.to_datetime(df["date"]).dt.date

        df = compute_metrics(df)

        inserted = 0
        for _, row in df.iterrows():
            existing = (
                db.query(StockPrice)
                .filter(
                    and_(StockPrice.symbol == symbol, StockPrice.date == row["date"])
                )
                .first()
            )

            if existing:
                continue

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

        db.commit()
        print(f"Inserted {inserted} new records for {symbol}")
        return inserted

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        db.rollback()
        return 0


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
            time.sleep(1)

        print(f"\nTotal new records inserted: {total_inserted}")

    finally:
        db.close()


if __name__ == "__main__":
    fetch_all_data()
