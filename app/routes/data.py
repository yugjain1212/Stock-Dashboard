from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Company, StockPrice
from app.schemas import StockPriceResponse, DataResponse

router = APIRouter()


@router.get("/data/{symbol}", response_model=DataResponse)
def get_stock_data(
    symbol: str, days: int = Query(default=30, le=365), db: Session = Depends(get_db)
):
    company = db.query(Company).filter(Company.symbol == symbol).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

    # Get the most recent `days` records, then reverse for ascending chart display
    prices = (
        db.query(StockPrice)
        .filter(StockPrice.symbol == symbol)
        .order_by(StockPrice.date.desc())
        .limit(days)
        .all()
    )
    prices = list(reversed(prices))

    data = [
        StockPriceResponse(
            id=p.id,
            symbol=p.symbol,
            date=p.date,
            open=p.open,
            high=p.high,
            low=p.low,
            close=p.close,
            volume=p.volume,
            daily_return=p.daily_return,
            moving_avg_7d=p.moving_avg_7d,
            week52_high=p.week52_high,
            week52_low=p.week52_low,
            volatility_score=p.volatility_score,
            created_at=p.created_at,
        )
        for p in prices
    ]

    return DataResponse(data=data, symbol=symbol, days=days)
