from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import func
from contextlib import asynccontextmanager
from app.database import SessionLocal, engine, Base
from app.models import StockPrice, Company
from app.routes import companies, data, summary, compare
from app.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        count = db.query(StockPrice).count()
        if count == 0:
            print("Database empty. Running fetcher...")
            from app.services.fetcher import fetch_all_data

            fetch_all_data()
        else:
            print(f"Database already has {count} records. Skipping fetch.")
    finally:
        db.close()

    yield

    print("Shutting down...")


app = FastAPI(
    title="Stock Data Intelligence Dashboard",
    description="Financial data intelligence platform for NSE/BSE Indian stock market",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(data.router, prefix="/api", tags=["data"])
app.include_router(summary.router, prefix="/api", tags=["summary"])
app.include_router(compare.router, prefix="/api", tags=["compare"])


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
def health_check():
    db = SessionLocal()
    try:
        count = db.query(StockPrice).count()
        latest = db.query(StockPrice).order_by(StockPrice.date.desc()).first()
        last_updated = latest.date.isoformat() if latest else None
        return HealthResponse(
            status="healthy", db_record_count=count, last_updated=last_updated
        )
    finally:
        db.close()


@app.get("/", tags=["frontend"])
def serve_frontend():
    return FileResponse("frontend/index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
