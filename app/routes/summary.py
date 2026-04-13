from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Company, StockPrice
from app.schemas import SummaryResponse

router = APIRouter()


@router.get("/summary/{symbol}", response_model=SummaryResponse)
def get_summary(symbol: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.symbol == symbol).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

    prices = (
        db.query(StockPrice)
        .filter(StockPrice.symbol == symbol)
        .order_by(StockPrice.date)
        .all()
    )

    if not prices:
        raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

    latest_price = prices[-1]

    last_30 = prices[-30:] if len(prices) >= 30 else prices

    avg_close = sum(p.close for p in last_30) / len(last_30)
    avg_volatility = sum(
        p.volatility_score for p in last_30 if p.volatility_score
    ) / len([p for p in last_30 if p.volatility_score])

    week52_high = max(p.week52_high for p in prices if p.week52_high)
    week52_low = min(p.week52_low for p in prices if p.week52_low)

    return SummaryResponse(
        symbol=symbol,
        name=company.name,
        week52_high=week52_high,
        week52_low=week52_low,
        avg_close=avg_close,
        latest_close=latest_price.close,
        latest_daily_return=latest_price.daily_return,
        avg_volatility_score=avg_volatility,
        total_trading_days=len(prices),
    )
