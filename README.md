# DB-LLM RAG Project

This project allows you to interact with various databases (Oracle, MySQL, SQLite) using natural language via LLMs (OpenAI-compatible or Hugging Face). It can generate SQL queries, execute them, and format the output according to your instructions.

## Features
- Natural language to SQL conversion.
- Automated execution on Oracle, MySQL, or SQLite.
- Support for OpenAI-compatible APIs (like Ollama, vLLM) and Hugging Face models.
- Customizable output formatting (e.g., tables, JSON, summaries).

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

    # Oracle config
    ORACLE_USER=your_user
    ORACLE_PASSWORD=your_password
    ORACLE_DSN=localhost:1521/your_service_name
    
    # MySQL config
    MYSQL_USER=your_mysql_user
    MYSQL_PASSWORD=your_mysql_password
    MYSQL_HOST=localhost
    MYSQL_PORT=3306
    MYSQL_DB=your_database

    # SQLite config
    SQLITE_PATH=demo.db

    # LLM selection: 'openai' or 'huggingface'
    LLM_TYPE=openai

    # OpenAI/Generic API config (Ollama, vLLM, etc.)
    LLM_API_KEY=your_llm_api_key (if needed)
    LLM_BASE_URL=http://localhost:11434/v1
    LLM_MODEL=llama3
    
    # Hugging Face config
    HF_MODEL_ID=google/flan-t5-large
    HF_TOKEN=your_huggingface_token (if needed for private/gated models)
    ```

3.  **Run the application**:
    ```bash
    export PYTHONPATH=$PYTHONPATH:.
    python3 src/main.py
    ```

## Usage
You can run it in interactive mode:
```bash
python3 src/main.py
```
Or pass a query directly:
```bash
python3 src/main.py "How many employees are in the sales department?"
```

## Project Structure
- `src/db_manager.py`: Handles database connections.
- `src/llm_manager.py`: Manages the connection to the LLM (OpenAI or Hugging Face).
- `src/oracle_bot.py`: Contains the core RAG and SQL generation logic.
- `src/main.py`: CLI entry point.
- `src/config.py`: Configuration management.
