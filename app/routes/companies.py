from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Company, StockPrice
from app.schemas import CompanyResponse

router = APIRouter()


@router.get("/", response_model=list[CompanyResponse])
def get_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.symbol).all()

    result = []
    for company in companies:
        latest_price = (
            db.query(StockPrice)
            .filter(StockPrice.symbol == company.symbol)
            .order_by(desc(StockPrice.date))
            .first()
        )

        result.append(
            CompanyResponse(
                symbol=company.symbol,
                name=company.name,
                sector=company.sector,
                market_cap_category=company.market_cap_category,
                latest_close=latest_price.close if latest_price else None,
                latest_daily_return=latest_price.daily_return if latest_price else None,
            )
        )

    return result
