# Oracle-Llama RAG Project

This project allows you to interact with an Oracle Database using natural language via the Llama LLM. It can generate SQL queries, execute them, and format the output according to your instructions.

## Features
- Natural language to SQL conversion.
- Automated execution on Oracle DB.
- Customizable output formatting (e.g., tables, JSON, summaries).
- Fallback to SQLite for demonstration and development.

## Setup

1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure environment variables**:
    Create a `.env` file with the following:
    ```env
    ORACLE_USER=your_user
    ORACLE_PASSWORD=your_password
    ORACLE_DSN=localhost:1521/your_service_name
    
    LLM_API_KEY=your_llm_api_key (if needed)
    LLM_BASE_URL=http://localhost:11434/v1 (e.g., for Ollama)
    LLM_MODEL=llama3
    
    USE_SQLITE=False # Set to True for demo
    ```

3.  **Run the application**:
    ```bash
    python -m src.main
    ```

## Usage
You can run it in interactive mode:
```bash
python -m src.main
```
Or pass a query directly:
```bash
python -m src.main "How many employees are in the sales department?"
```

## Project Structure
- `src/db_manager.py`: Handles database connections.
- `src/llm_manager.py`: Manages the connection to the Llama model.
- `src/oracle_bot.py`: Contains the core RAG and SQL generation logic.
- `src/main.py`: CLI entry point.
