from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from src.db_manager import DBManager
from src.llm_manager import LLMManager
from src.oracle_bot import OracleBot
from src.config import Config
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

app = FastAPI(title="DB-LLM RAG API", description="API to interact with databases using natural language")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
bot = None

@app.on_event("startup")
async def startup_event():
    global bot
    db_manager = DBManager(db_type=Config.DB_TYPE, include_tables=Config.INCLUDE_TABLES)
    llm_manager = LLMManager(llm_type=Config.LLM_TYPE)
    bot = OracleBot(db_manager, llm_manager)
    print("Bot initialized and ready for API requests.")

class QueryRequest(BaseModel):
    question: str
    format_instruction: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sql_queries: List[str]
    report_id: Optional[str] = None
    error: Optional[str] = None

@app.post("/ask", response_model=QueryResponse)
def ask(request: QueryRequest):
    """
    Handles natural language queries.
    Defined as 'def' (not 'async def') to run in a threadpool,
    allowing multiple concurrent requests without blocking the event loop.
    """
    if bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    try:
        result = bot.ask(request.question, request.format_instruction)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports")
async def list_reports():
    if bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    return bot.reports_manager.reports

@app.get("/health")
async def health_check():
    return {"status": "healthy", "db_type": Config.DB_TYPE, "llm_type": Config.LLM_TYPE}

# Serve static files for the frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def read_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not found in src/static/"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
