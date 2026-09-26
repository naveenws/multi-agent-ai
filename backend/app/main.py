from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import router as api_router
from app.database.db import create_db_and_tables

app = FastAPI(
    title="Multi-Agent AI Orchestrator",
    description="Adaptive Multi-Agent AI Orchestration System",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

import os
from sqlalchemy.sql import text

FRONTEND_URL = os.getenv("FRONTEND_URL")
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]
if FRONTEND_URL:
    origins.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to the Adaptive Multi-Agent AI Orchestration System API"}

@app.get("/health")
async def health_check():
    try:
        from app.database.db import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "database": db_status
    }

