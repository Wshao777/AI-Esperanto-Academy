# backend/services/payment_engine.py
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re

class PaymentEngine:
    """收款規則引擎 - 30萬美金月費專用"""
    
    # 收款關鍵詞規則
    PAYMENT_RULES = [
        {
            "keyword": r"(?i)(?:月費|月租|monthly fee|subscription)",
            "risk_level": "中",
            "category": "經常性費用",
            "suggestion": "確認每月300,000 USD是否含稅、調漲機制"
        },
        {
            "keyword": r"(?i)(?:30萬|300,000|300000|thirty|usd 300k)",
            "risk_level": "高",
            "category": "費用金額",
            "suggestion": "確認計價幣別、匯率風險、付款期限"
        },
        {
            "keyword": r"(?i)(?:逾期|滯納金|late payment|penalty)",
            "risk_level": "高",
            "category": "違約金",
            "suggestion": "逾期利率是否超過年利率20%？"
        },
        {
            "keyword": r"(?i)(?:預付|prepay|advance payment)",
            "risk_level": "中",
            "category": "付款條件",
            "suggestion": "預付週期是否為一個月？"
        },
        {
            "keyword": r"(?i)(?:發票|invoice|billing)",
            "risk_level": "低",
            "category": "請款程序",
            "suggestion": "發票開立時程、買受人資訊"
        }
    ]
    
    @classmethod
    def analyze_payment_clauses(cls, text: str) -> Dict[str, Any]:
        """分析合約中的收款條款"""
        findings = []
        lines = text.splitlines()
        
        for rule in cls.PAYMENT_RULES:
            pattern = re.compile(rule["keyword"])
            for idx, line in enumerate(lines, 1):
                if pattern.search(line):
                    findings.append({
                        "line": idx,
                        "text": line.strip()[:80],
                        "matched_keyword": rule["keyword"].replace("(?i)", ""),
                        "risk_level": rule["risk_level"],
                        "category": rule["category"],
                        "suggestion": rule["suggestion"]
                    })
        
        # 萃取付款金額與週期
        amount_match = re.search(r"(?i)(?:30萬|300[,\s]?000|300000)", text)
        period_match = re.search(r"(?i)(?:月|month|per month)", text)
        
        return {
            "has_payment_clause": len(findings) > 0,
            "findings": findings,
            "detected_amount": "300,000 USD" if amount_match else "未明確",
            "detected_period": "每月" if period_match else "未明確",
            "total_monthly": 300000.00,
            "currency": "USD",
            "risk_summary": self._generate_summary(findings)
        }
    
    @classmethod
    def _generate_summary(cls, findings: List[Dict]) -> str:
        high_risks = [f for f in findings if f["risk_level"] == "高"]
        if high_risks:
            return f"⚠️ 發現 {len(high_risks)} 項高風險收款條款，建議優先確認"
        return "✅ 收款條款無明顯高風險"
    
    @classmethod
    def calculate_payment_schedule(cls, start_date: str, months: int = 12) -> List[Dict]:
        """產生未來12個月的收款時程表"""
        schedule = []
        current = datetime.strptime(start_date, "%Y-%m-%d")
        
        for i in range(months):
            due_date = current + timedelta(days=30 * i)
            schedule.append({
                "period": f"第{i+1}期",
                "due_date": due_date.strftime("%Y-%m-%d"),
                "amount_usd": 300000,
                "amount_twd": round(300000 * 31.5),  # 假設匯率31.5
                "status": "待收款" if i > 0 else "本月應收"
            })
        return schedule


class PaymentManager:
    """收款管理 - 30萬美金月費"""
    
    def __init__(self):
        self.total_monthly_fee = 300000.00
        self.currency = "USD"
    
    def get_payment_summary(self, contract_id: str) -> Dict[str, Any]:
        """取得合約收款總覽"""
        return {
            "contract_id": contract_id,
            "monthly_fee": self.total_monthly_fee,
            "currency": self.currency,
            "annual_revenue": self.total_monthly_fee * 12,
            "payment_terms": "月付，每月1日前預付",
            "late_penalty": "年利率12%",
            "next_payment_date": datetime.now().strftime("%Y-%m-01"),
            "total_received": 0.00,
            "pending_amount": 300000.00
        }
    
    def record_payment(self, contract_id: str, amount: float, payment_date: str):
        """記錄收款（可串接資料庫）"""
        # 此處可擴充為寫入資料庫
        return {
            "success": True,
            "contract_id": contract_id,
            "amount": amount,
            "payment_date": payment_date,
            "message": "收款紀錄成功"
        }

# 測試
if __name__ == "__main__":
    sample = """
    乙方應於每月1日前支付甲方月費 USD 300,000。
    逾期未付者，應按日加計年利率12%之滯納金。
    甲方應於收款後5日內開立發票。
    """
    result = PaymentEngine.analyze_payment_clauses(sample)
    print("🔍 收款條款分析：", result)
    
    schedule = PaymentEngine.calculate_payment_schedule("2026-03-01")
    print("📅 收款時程表：", schedule[:2])
import os
import json
import logging
import asyncio
from typing import List

import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, BaseSettings
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Numeric, DateTime, func
from sqlalchemy.ext.declardeclarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Settings
class Settings(BaseSettings):
    database_url: str = "postgresql://user:password@postgres:5432/dispatch_db"
    redis_url: str = "redis://redis:6379/0"

    class Config:
        env_file = ".env"

settings = Settings()

# Database Setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Models ---
class Library(Base):
    __tablename__ = "libraries"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    active = Column(Boolean, default=True)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True)
    library_id = Column(Integer, index=True)
    status = Column(String, default="pending") # pending, success, failed
    amount = Column(Numeric(10, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class OrderError(Base):
    __tablename__ = "order_errors"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, index=True)
    library_id = Column(Integer, index=True)
    fail_reason = Column(String)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Create tables
Base.metadata.create_all(bind=engine)

# --- Pydantic Models ---
class WebhookPayload(BaseModel):
    order_id: str
    library_id: int
    amount: float
    customer_details: dict

class LibraryModel(BaseModel):
    id: int
    name: str
    active: bool

    class Config:
        orm_mode = True

# --- FastAPI App ---
app = FastAPI(title="Automated Dispatch System API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis Connection
@app.on_event("startup")
async def startup_event():
    app.state.redis = await redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.redis.close()

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# --- API Endpoints ---
@app.post("/api/webhook")
async def receive_webhook(payload: WebhookPayload):
    """
    Receives an order from a third-party, places it into the Redis queue.
    """
    try:
        await app.state.redis.lpush("incoming_orders", payload.json())
        await manager.broadcast(json.dumps({"type": "new_order", "order_id": payload.order_id}))
        return {"status": "success", "message": "Order queued for processing."}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue order.")

@app.get("/api/status")
async def get_system_status():
    """
    Returns current system status, including queue lengths.
    """
    incoming_queue_len = await app.state.redis.llen("incoming_orders")
    dlq_len = await app.state.redis.llen("failed_orders")
    return {
        "incoming_queue_length": incoming_queue_len,
        "dead_letter_queue_length": dlq_len
    }

@app.post("/api/replay-dlq")
async def replay_dead_letter_queue():
    """
    Moves all items from the DLQ back to the main incoming queue for reprocessing.
    """
    count = 0
    while True:
        job = await app.state.redis.rpop("failed_orders")
        if not job:
            break
        await app.state.redis.lpush("incoming_orders", job)
        count += 1
    
    message = f"Re-queued {count} jobs from the DLQ."
    await manager.broadcast(json.dumps({"type": "dlq_replayed", "count": count}))
    logger.info(message)
    return {"status": "success", "message": message}

@app.get("/api/libraries", response_model=List[LibraryModel])
def get_libraries():
    """
    Returns a list of all libraries.
    """
    db = SessionLocal()
    libraries = db.query(Library).all()
    db.close()
    return libraries

@app.get("/api/dlq-items")
async def get_dlq_items():
    """
    Returns all items currently in the dead-letter queue.
    """
    items = await app.state.redis.lrange("failed_orders", 0, -1)
    return [json.loads(item) for item in items]

@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from WebSocket.")

if __name__ == "__main__":
    import uvicorn
    # This part is for local development without Docker
    uvicorn.run(app, host="0.0.0.0", port=8000)