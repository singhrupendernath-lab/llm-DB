import hashlib
import time
import sqlalchemy

from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase

try:
    from langchain.memory import ConversationBufferWindowMemory
except ImportError:
    try:
        from langchain_classic.memory import ConversationBufferWindowMemory
    except ImportError:
        from langchain_community.memory import ConversationBufferWindowMemory

try:
    from langchain.agents.agent_types import AgentType
except ImportError:
    try:
        from langchain_classic.agents.agent_types import AgentType
    except ImportError:
        class AgentType:
            ZERO_SHOT_REACT_DESCRIPTION = "zero-shot-react-description"
            OPENAI_FUNCTIONS = "openai-functions"

from src.db_manager import DBManager
from src.llm_manager import LLMManager
from src.reports_manager import ReportsManager
from src.vector_manager import VectorManager


class OracleBot:
    CACHE_TTL = 300  # 5 minutes cache expiry

    def __init__(self, db_manager: DBManager, llm_manager: LLMManager):
        self.db_manager = db_manager
        self.llm_manager = llm_manager
        self.llm = self.llm_manager.get_llm()

        self.reports_manager = ReportsManager()
        self.vector_manager = VectorManager(db_manager)

        self.memories = {}
        self.executors = {}
        self.response_cache = {}

    # -------------------------------
    # Utility Functions
    # -------------------------------

    def _normalize_question(self, question: str):
        return " ".join(question.lower().strip().split())

    def _hash_question(self, question: str):
        normalized = self._normalize_question(question)
        return hashlib.md5(normalized.encode()).hexdigest()

    def _get_memory(self, session_id):
        if session_id not in self.memories:
            self.memories[session_id] = ConversationBufferWindowMemory(
                memory_key="chat_history",
                return_messages=True,
                k=3
            )
        return self.memories[session_id]

    def _get_cached_response(self, session_id, question_hash):
        session_cache = self.response_cache.get(session_id, {})
        cached = session_cache.get(question_hash)

        if cached:
            if time.time() - cached["timestamp"] < self.CACHE_TTL:
                return cached
        return None

    def _store_cache(self, session_id, question_hash, answer, sql_queries):
        session_cache = self.response_cache.setdefault(session_id, {})
        session_cache[question_hash] = {
            "answer": answer,
            "sql_queries": sql_queries,
            "timestamp": time.time()
        }

    # -------------------------------
    # Agent Creation
    # -------------------------------

    def _create_agent_executor(self, session_id, include_tables=None):
        memory = self._get_memory(session_id)

        db = SQLDatabase(
            self.db_manager.engine,
            include_tables=include_tables,
            sample_rows_in_table_info=1
        )

        # Oracle semicolon fix
        if self.db_manager.db_type == "oracle":
            original_run = db.run

            def wrapped_run(command, *args, **kwargs):
                if isinstance(command, str):
                    command = command.strip().rstrip(";")
                return original_run(command, *args, **kwargs)

            db.run = wrapped_run

        if self.llm_manager.llm_type == "openai":
            agent_type = "tool-calling"
        else:
            agent_type = AgentType.ZERO_SHOT_REACT_DESCRIPTION

        return create_sql_agent(
            llm=self.llm,
            db=db,
            verbose=False,  # faster
            agent_type=agent_type,
            max_iterations=10,  # reduce reasoning steps
            early_stopping_method="generate",
            agent_executor_kwargs={
                "memory": memory,
                "handle_parsing_errors": True
            }
        )

    # -------------------------------
    # Main Ask Method
    # -------------------------------

    def ask(self, question: str, format_instruction: str = None, session_id: str = "default"):

        question_hash = self._hash_question(question)

        # 🔥 1. Check Cache First
        cached = self._get_cached_response(session_id, question_hash)
        if cached:
            return {
                "answer": cached["answer"],
                "sql_queries": cached["sql_queries"],
                "cached": True
            }

        # 🔥 2. Predefined Reports
        report_id = self.reports_manager.find_report_id(question)
        if report_id:
            report = self.reports_manager.get_report(report_id)
            missing = self.reports_manager.get_missing_variables(report_id, question)

            if missing:
                return {
                    "answer": f"Report '{report['name']}' requires: {', '.join(missing)}",
                    "sql_queries": []
                }

            query = self.reports_manager.format_query(report_id, question)

            try:
                with self.db_manager.engine.connect() as conn:
                    data = conn.execute(sqlalchemy.text(query)).fetchall()

                if not data:
                    return {
                        "answer": "No records found.",
                        "sql_queries": [query],
                        "report_id": report_id
                    }

                format_prompt = (
                    f"Convert this into clean Markdown table only:\n{data}"
                )

                response = self.llm.invoke(format_prompt) if hasattr(self.llm, 'invoke') else self.llm(format_prompt)
                answer = response.content if hasattr(response, 'content') else str(response)

                self._store_cache(session_id, question_hash, answer, [query])

                return {
                    "answer": answer,
                    "sql_queries": [query],
                    "report_id": report_id
                }

            except Exception as e:
                return {"answer": f"Error: {str(e)}", "sql_queries": []}

        # 🔥 3. RAG Table Selection
        relevant_tables = self.vector_manager.get_relevant_tables(question)

        # 🔥 4. Reuse Executor if Exists
        if session_id not in self.executors:
            self.executors[session_id] = self._create_agent_executor(
                session_id,
                include_tables=relevant_tables
            )

        agent_executor = self.executors[session_id]

        full_query = question
        if format_instruction:
            full_query += f"\nFormat output as: {format_instruction}"

        try:
            result = agent_executor.invoke({"input": full_query})

            sql_queries = []
            for step in result.get("intermediate_steps", []):
                if hasattr(step[0], 'tool') and step[0].tool == "sql_db_query":
                    sql_queries.append(step[0].tool_input)

            answer = result["output"]

            # 🔥 Store in Cache
            self._store_cache(session_id, question_hash, answer, sql_queries)

            return {
                "answer": answer,
                "sql_queries": sql_queries
            }

        except Exception as e:
            return {
                "answer": f"Error occurred: {str(e)}",
                "sql_queries": []
            }
