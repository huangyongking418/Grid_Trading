import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth import get_current_user, can_view_all
from app.models.all_models import Stock, StrategyInstance
from app.services.bind_service import bind_instance_to_stock, unbind_instance
from app.schemas.stock import StockCreate, StockOut, StockBind, StockSearchOut

router = APIRouter(prefix="/api/stocks", tags=["标的管理"])

# 东方财富搜索建议接口（免费、无需密钥；覆盖 A股股票 + 场内基金/ETF）
EASTMONEY_SUGGEST_URL = "https://searchapi.eastmoney.com/api/suggest/get"
EASTMONEY_TOKEN = "D43BF722C8E33BDC906FB84D85E326E8"

_A_STOCK_TYPES = ("沪A", "深A", "京A", "沪深A股")
_FUND_TYPES = ("基金",)
# 场内基金/ETF 代码特征：沪市 5xxxxx，深市 15/16/18xxxx
_ETF_CODE_PREFIXES = ("5", "15", "16", "18")


def _is_etf_code(code: str) -> bool:
    return len(code) == 6 and code.startswith(_ETF_CODE_PREFIXES)


def _search_market(keyword: str) -> List[dict]:
    """调用东方财富搜索建议接口，返回 A股股票 / ETF 列表（网络异常返回空列表）。"""
    try:
        resp = httpx.get(
            EASTMONEY_SUGGEST_URL,
            params={
                "input": keyword,
                "type": 14,
                "token": EASTMONEY_TOKEN,
                "count": 20,
            },
            timeout=5.0,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        resp.raise_for_status()
        data = resp.json()
        items = (data.get("QuotationCodeTable") or {}).get("Data") or []
        results = []
        seen = set()
        for item in items:
            code = str(item.get("Code") or "").strip()
            name = str(item.get("Name") or "").strip()
            sec_type = str(item.get("SecurityTypeName") or "").strip()
            if not code or not name or code in seen:
                continue
            if sec_type in _A_STOCK_TYPES:
                results.append({"code": code, "name": name, "type": "stock"})
                seen.add(code)
            elif sec_type in _FUND_TYPES and _is_etf_code(code):
                results.append({"code": code, "name": name, "type": "etf"})
                seen.add(code)
        return results
    except Exception:
        return []


@router.get("", response_model=List[StockOut])
def list_stocks(db: Session = Depends(get_db), current=Depends(get_current_user)):
    q = db.query(Stock)
    if not can_view_all(current):
        q = q.filter(Stock.user_id == current.id)
    return q.order_by(Stock.code).all()


@router.get("/search", response_model=List[StockSearchOut])
def search_stocks(
    keyword: str = Query(..., min_length=1, max_length=32),
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    """按代码/名称搜索 A股股票与 ETF（东方财富实时数据源），已收录的本地标的附带 stock_id。"""
    kw = keyword.strip()
    if not kw:
        return []
    remote_items = _search_market(kw)
    local_q = db.query(Stock).filter(
        or_(Stock.code.like(f"%{kw}%"), Stock.name.like(f"%{kw}%"))
    )
    if not can_view_all(current):
        local_q = local_q.filter(Stock.user_id == current.id)
    local_map = {s.code: s for s in local_q.all()}
    seen = set()
    results: List[StockSearchOut] = []
    for item in remote_items:
        seen.add(item["code"])
        stock = local_map.get(item["code"])
        results.append(
            StockSearchOut(
                code=item["code"],
                name=item["name"],
                type=item["type"],
                stock_id=stock.id if stock else None,
            )
        )
    for code, stock in local_map.items():
        if code not in seen:
            results.append(
                StockSearchOut(code=stock.code, name=stock.name, type=stock.type, stock_id=stock.id)
            )
    return results


@router.post("", response_model=StockOut, status_code=201)
def create_stock(data: StockCreate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    existing = db.query(Stock).filter(Stock.code == data.code, Stock.user_id == current.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="标的代码已存在")
    stock = Stock(**data.model_dump(), user_id=current.id)
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return stock


@router.delete("/{stock_id}", status_code=204)
def delete_stock(stock_id: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    q = db.query(Stock).filter(Stock.id == stock_id)
    if not can_view_all(current):
        q = q.filter(Stock.user_id == current.id)
    stock = q.first()
    if not stock:
        raise HTTPException(status_code=404, detail="标的不存在")
    if stock.strategy_instance_id:
        db.query(StrategyInstance).filter(
            StrategyInstance.id == stock.strategy_instance_id
        ).update({"stock_id": None})
    db.delete(stock)
    db.commit()
    return None


@router.post("/{stock_id}/bind", response_model=StockOut)
def bind_strategy(stock_id: int, data: StockBind, db: Session = Depends(get_db), current=Depends(get_current_user)):
    q = db.query(Stock).filter(Stock.id == stock_id)
    if not can_view_all(current):
        q = q.filter(Stock.user_id == current.id)
    stock = q.first()
    if not stock:
        raise HTTPException(status_code=404, detail="标的不存在")
    instance = db.query(StrategyInstance).filter(
        StrategyInstance.id == data.instance_id,
        StrategyInstance.user_id == current.id,
    ).first()
    if not instance:
        raise HTTPException(status_code=404, detail="策略实例不存在")
    bind_instance_to_stock(db, instance, stock)
    db.commit()
    db.refresh(stock)
    return stock


@router.post("/{stock_id}/unbind", response_model=StockOut)
def unbind_strategy(stock_id: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    q = db.query(Stock).filter(Stock.id == stock_id)
    if not can_view_all(current):
        q = q.filter(Stock.user_id == current.id)
    stock = q.first()
    if not stock:
        raise HTTPException(status_code=404, detail="标的不存在")
    if stock.strategy_instance_id:
        instance = db.query(StrategyInstance).filter(
            StrategyInstance.id == stock.strategy_instance_id
        ).first()
        if instance:
            unbind_instance(db, instance)
        else:
            stock.strategy_instance_id = None
    db.commit()
    db.refresh(stock)
    return stock
