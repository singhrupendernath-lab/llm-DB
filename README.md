# DB-LLM RAG Project

This project allows you to interact with various databases (Oracle, MySQL, SQLite) using natural language via LLMs (OpenAI-compatible, Hugging Face local, or GGUF). It can generate SQL queries, execute them, and format the output according to your instructions.

## Features
- Natural language to SQL conversion.
- Automated execution on Oracle, MySQL, or SQLite.
- Support for OpenAI-compatible APIs (like Ollama, vLLM).
- Support for local Hugging Face models (CausalLM and Seq2Seq).
- Support for **GGUF** models via `llama-cpp-python`.
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
    
    # LLM selection: 'openai', 'huggingface', or 'llamacpp'
    LLM_TYPE=llamacpp

    # LlamaCpp / GGUF config
    # The application will automatically download the model from HF if LOCAL_MODEL_PATH is empty
    HF_GGUF_REPO=bartowski/Meta-Llama-3.1-8B-Instruct-GGUF
    HF_GGUF_FILE=Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
    # HF_TOKEN=your_huggingface_token (required for gated models like Llama 3)

    # Alternatively, specify a local path:
    # LOCAL_MODEL_PATH=models/llama-3-8b-instruct.gguf
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
python3 src/main.py "How many students are in the database?"
```

## Project Structure
- `src/db_manager.py`: Handles database connections.
- `src/llm_manager.py`: Manages the connection to the LLM (OpenAI, Transformers, or LlamaCpp).
- `src/oracle_bot.py`: Contains the core RAG and SQL generation logic using LangChain SQL Agent.
- `src/main.py`: CLI entry point.
- `src/config.py`: Configuration management.
