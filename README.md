# DB-LLM RAG Project

This project allows you to interact with various databases (Oracle, MySQL, SQLite) using natural language via LLMs (OpenAI-compatible, Hugging Face local, Hugging Face API, or GGUF). It can generate SQL queries, execute them, and format the output according to your instructions.

## Features
- Natural language to SQL conversion.
- Automated execution on Oracle, MySQL, or SQLite.
- Support for OpenAI-compatible APIs (like Ollama, vLLM).
- Support for local Hugging Face models (CausalLM and Seq2Seq).
- Support for **Hugging Face Inference API** (Fastest for open source models).
- Support for **GGUF** models via `llama-cpp-python`.
- Conversation memory for multi-turn sessions.
- **Predefined Reports**: Execute specific SQL queries by providing a report ID (e.g., "AT1201").
- Customizable output formatting (e.g., Markdown tables, lists).
- Captures and displays executed SQL queries for transparency.

## Setup

1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure environment variables**:
    Create a `.env` file with the following:
    ```env
    # Database selection: 'sqlite', 'oracle', or 'mysql'
    DB_TYPE=sqlite
    
    # MySQL config
    MYSQL_USER=your_mysql_user
    MYSQL_PASSWORD=your_mysql_password
    MYSQL_HOST=localhost
    MYSQL_PORT=3306
    MYSQL_DB=your_database
    
    # SQLite config
    SQLITE_PATH=demo.db

    # LLM selection: 'openai', 'huggingface', 'llamacpp', or 'huggingface_api'
    LLM_TYPE=huggingface_api

    # --- Hugging Face Inference API config ---
    # Model ID (e.g., 'meta-llama/Llama-3.1-8B-Instruct')
    HF_MODEL_ID=meta-llama/Llama-3.1-8B-Instruct
    HF_TOKEN=your_huggingface_token
    # Tip: Some API providers (like Novita) require a specific task.
    # If you get a 'task not supported' error, try:
    HF_TASK=conversational

    # --- GGUF / LlamaCpp config ---
    # LLM_TYPE=llamacpp
    # HF_GGUF_REPO=bartowski/Meta-Llama-3.1-8B-Instruct-GGUF
    # HF_GGUF_FILE=Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
    ```

3.  **Run the application**:
    ```bash
    export PYTHONPATH=$PYTHONPATH:.
    python3 src/main.py
    ```

## Predefined Reports
You can define specific SQL queries for report IDs in the `reports.json` file. When a user mentions a report ID (e.g., "I want AT1201 reports"), the bot will skip the reasoning process and execute the mapped query directly.

Example `reports.json`:
```json
{
    "AT1201": {
        "name": "Student Attendance Report",
        "query": "SELECT s.name, s.roll_no, sa.status FROM student_attendance sa JOIN students s ON s.id = sa.student_id WHERE sa.date = '2024-09-01';"
    }
}
```
All executions of predefined reports are logged to `report_execution.log`.

## Usage
You can run it in interactive mode:
```bash
python3 src/main.py
```
Or pass a query directly:
```bash
python3 src/main.py "How many students are in the database?"
```

## Project Structure
- `src/db_manager.py`: Handles database connections.
- `src/llm_manager.py`: Manages the connection to the LLM.
- `src/oracle_bot.py`: Contains the core RAG and SQL generation logic using LangChain SQL Agent.
- `src/main.py`: CLI entry point.
- `src/config.py`: Configuration management.
