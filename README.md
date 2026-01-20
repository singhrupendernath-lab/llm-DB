# DB-LLM RAG Project

This project allows you to interact with various databases (Oracle, MySQL, SQLite) using natural language via LLMs (OpenAI-compatible, Hugging Face local, or GGUF). It can generate SQL queries, execute them, and format the output according to your instructions.

## Features
- Natural language to SQL conversion.
- Automated execution on Oracle, MySQL, or SQLite.
- Support for OpenAI-compatible APIs (like Ollama, vLLM).
- Support for local Hugging Face models (CausalLM and Seq2Seq).
- Support for **GGUF** models (e.g., Llama 3) via `transformers` and `gguf`.
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
    LLM_API_KEY=your_api_key_if_needed
    LLM_BASE_URL=http://localhost:11434/v1
    LLM_MODEL=llama3
    
    # Hugging Face / GGUF config
    # Default is a capable small model
    HF_MODEL_ID=Qwen/Qwen2.5-1.5B-Instruct
    HF_TOKEN=your_huggingface_token
    HF_MAX_LENGTH=2048

    # For Llama 3 (GGUF):
    # Note: Llama 3 is gated. You must accept the license on HF and use a valid HF_TOKEN.
    # HF_MODEL_ID=bartowski/Meta-Llama-3.1-8B-Instruct-GGUF
    # HF_GGUF_FILE=Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
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
- `src/llm_manager.py`: Manages the connection to the LLM.
- `src/oracle_bot.py`: Contains the core RAG and SQL generation logic.
- `src/main.py`: CLI entry point.
- `src/config.py`: Configuration management.
