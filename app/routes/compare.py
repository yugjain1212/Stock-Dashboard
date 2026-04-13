from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Company, StockPrice
from app.schemas import CompareResponse, CompareStats
import numpy as np

router = APIRouter()


def compute_stats(prices, symbol):
    if not prices:
        return None

    closes = [p.close for p in prices]
    daily_returns = [p.daily_return for p in prices if p.daily_return is not None]
    volatilities = [
        p.volatility_score for p in prices if p.volatility_score is not None
    ]

    avg_close = sum(closes) / len(closes)
    total_return_pct = ((closes[-1] - closes[0]) / closes[0]) * 100 if closes[0] else 0
    max_close = max(closes)
    min_close = min(closes)
    avg_volatility = sum(volatilities) / len(volatilities) if volatilities else 0

    return CompareStats(
        symbol=symbol,
        avg_close=avg_close,
        total_return_pct=total_return_pct,
        max_close=max_close,
        min_close=min_close,
        avg_volatility=avg_volatility,
    )


@router.get("/compare", response_model=CompareResponse)
def compare_symbols(
    symbol1: str = Query(...),
    symbol2: str = Query(...),
    days: int = Query(default=30, le=365),
    db: Session = Depends(get_db),
):
    company1 = db.query(Company).filter(Company.symbol == symbol1).first()
    company2 = db.query(Company).filter(Company.symbol == symbol2).first()

    if not company1:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol1} not found")
    if not company2:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol2} not found")

    prices1 = (
        db.query(StockPrice)
        .filter(StockPrice.symbol == symbol1)
        .order_by(StockPrice.date)
        .limit(days)
        .all()
    )

    prices2 = (
        db.query(StockPrice)
        .filter(StockPrice.symbol == symbol2)
        .order_by(StockPrice.date)
        .limit(days)
        .all()
    )

    stats1 = compute_stats(prices1, symbol1)
    stats2 = compute_stats(prices2, symbol2)

    if not stats1 or not stats2:
        raise HTTPException(status_code=404, detail="Insufficient data for comparison")

    returns1 = [p.daily_return for p in prices1 if p.daily_return is not None]
    returns2 = [p.daily_return for p in prices2 if p.daily_return is not None]

    min_len = min(len(returns1), len(returns2))
    if min_len > 0:
        correlation = float(np.corrcoef(returns1[:min_len], returns2[:min_len])[0, 1])
    else:
        correlation = 0.0

    better = symbol1 if stats1.total_return_pct > stats2.total_return_pct else symbol2

    return CompareResponse(
        symbol1_stats=stats1,
        symbol2_stats=stats2,
        correlation=correlation,
        better_performer=better,
    )
