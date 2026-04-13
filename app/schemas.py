from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class CompanyBase(BaseModel):
    symbol: str
    name: str
    sector: str
    market_cap_category: str


class CompanyResponse(CompanyBase):
    latest_close: Optional[float] = None
    latest_daily_return: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class StockPriceResponse(BaseModel):
    id: int
    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    daily_return: Optional[float] = None
    moving_avg_7d: Optional[float] = None
    week52_high: Optional[float] = None
    week52_low: Optional[float] = None
    volatility_score: Optional[float] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DataResponse(BaseModel):
    data: List[StockPriceResponse]
    symbol: str
    days: int


class SummaryResponse(BaseModel):
    symbol: str
    name: str
    week52_high: float
    week52_low: float
    avg_close: float
    latest_close: float
    latest_daily_return: float
    avg_volatility_score: float
    total_trading_days: int


class CompareStats(BaseModel):
    symbol: str
    avg_close: float
    total_return_pct: float
    max_close: float
    min_close: float
    avg_volatility: float


class CompareResponse(BaseModel):
    symbol1_stats: CompareStats
    symbol2_stats: CompareStats
    correlation: float
    better_performer: str


class HealthResponse(BaseModel):
    status: str
    db_record_count: int
    last_updated: Optional[str] = None


class CompanyListResponse(BaseModel):
    companies: List[CompanyResponse]
