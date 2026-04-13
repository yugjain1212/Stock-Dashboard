from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import func
from contextlib import asynccontextmanager
from app.database import SessionLocal, engine, Base
from app.models import StockPrice, Company
from app.routes import companies, data, summary, compare
from app.schemas import HealthResponse
from app.services.fetcher import fetch_all_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("Database ready.")

    db = SessionLocal()
    try:
        record_count = db.query(StockPrice).count()
        print(f"Current records: {record_count}")

        if record_count == 0:
            print("No data found. Fetching stock data...")
            fetch_all_data()
        else:
            print("Data already exists, skipping fetch.")
    except Exception as e:
        print(f"Error checking data: {e}")
    finally:
        db.close()

    print("App ready.")
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
