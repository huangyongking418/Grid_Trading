from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.database import engine, Base
from app.api.strategies import router as strategies_router
from app.api.stocks import router as stocks_router
from app.api.monitor import router as monitor_router
from app.api.profit import router as profit_router
from app.api.reset import router as reset_router
from app.api.messages import router as messages_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.roles import router as roles_router
from app.api.params import router as params_router
from app.api.announcements import router as announcements_router
from app.api.grid import router as grid_router
from app.api.scheduler import router as scheduler_router
from app.api.backtest import router as backtest_router
from app.api.documents import router as documents_router
from app.api.system_config import router as system_config_router
from app.services import scheduler_manager


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """?????????????????????????? Alembic?"""
    Base.metadata.create_all(bind=engine)
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        scheduler_manager.start(db)
    except Exception:
        pass
    finally:
        db.close()
    yield
    try:
        scheduler_manager.shutdown()
    except Exception:
        pass


app = FastAPI(
    title="?????? API",
    description="Grid Trading System - ???? / ?? / ????",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(strategies_router)
app.include_router(stocks_router)
app.include_router(grid_router)
app.include_router(reset_router)
app.include_router(messages_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(params_router)
app.include_router(announcements_router)
app.include_router(profit_router)
app.include_router(monitor_router)
app.include_router(scheduler_router)
app.include_router(backtest_router)
app.include_router(documents_router)
app.include_router(system_config_router)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/health")
def health():
    return {"status": "ok", "service": "grid-trading-system"}


@app.get("/api/config")
def get_config():
    from app.core.config import settings
    return {
        "market_data_mode": settings.market_data_mode,
    }
