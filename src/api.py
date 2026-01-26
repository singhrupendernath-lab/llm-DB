from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from db_manager import DBManager
from llm_manager import LLMManager
from oracle_bot import OracleBot
from config import Config
import uvicorn

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
async def ask(request: QueryRequest):
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
