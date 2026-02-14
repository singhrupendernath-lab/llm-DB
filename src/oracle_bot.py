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

    def _create_agent_executor(self, session_id, include_tables=None, extra_context=None):
        memory = self._get_memory(session_id)

        # Create/Get a dynamic DB instance with only relevant tables (Optimized)
        db = self.db_manager.get_db(include_tables=include_tables)

        if self.llm_manager.llm_type == "openai":
            agent_type = "tool-calling"
        else:
            agent_type = AgentType.ZERO_SHOT_REACT_DESCRIPTION

        table_names_str = ", ".join(include_tables) if include_tables else "all tables"

        prefix = (
            "You are an expert SQL Data Analyst. Relevant tables: {table_names_str}.\n"
            "Dialect: {dialect}. Top K: {top_k}.\n"
            "History: {{chat_history}}\n"
        ).replace("{table_names_str}", table_names_str)

        if extra_context:
            prefix += f"\n{extra_context}\n"

        prefix += (
            "\nRULES:\n"
            "1. Greets? Answer direct.\n"
            "2. DB query? Use 'sql_db_schema' first.\n"
            "3. ONLY use tools below. NO hallucinations.\n"
            "4. STOP after 'Action Input:'.\n"
            "5. NO new questions after 'Final Answer'.\n"
        )

        if agent_type == AgentType.ZERO_SHOT_REACT_DESCRIPTION:
            prefix += (
                "FORMAT:\n"
                "Thought: [reasoning]\n"
                "Action: [tool]\n"
                "Action Input: [input]\n"
                "Observation: [system result]\n"
                "... (repeat if needed)\n"
                "Thought: I have the answer\n"
                "Final Answer: [Markdown answer]\n"
            )
            suffix = (
                "Begin!\n\n"
                "Question: {input}\n"
                "{agent_scratchpad}"
            )
        else:
            suffix = None

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
        # Generate question embedding once (Optimization)
        question_vector = self.vector_manager.get_embedding(question)

        # Retrieve relevant past interactions for self-learning (Optimized)
        extra_context = self.vector_manager.search_relevant_chat_by_vector(question_vector)

        # Check for predefined reports first
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
                if extra_context:
                    format_prompt = f"{extra_context}\n\n" + format_prompt

                if format_instruction:
                    format_prompt += f"\nNote: {format_instruction}"

                response = self.llm.invoke(format_prompt) if hasattr(self.llm, 'invoke') else self.llm(format_prompt)
                answer = response.content if hasattr(response, 'content') else str(response)

                self._store_cache(session_id, question_hash, answer, [query])

                # Save to vector DB for self-learning (Asynchronous)
                self.vector_manager.add_chat_interaction(question, answer, [query], session_id)

                return {
                    "answer": answer,
                    "sql_queries": [query],
                    "report_id": report_id
                }

        # RAG: Find relevant tables (Optimized)
        relevant_tables = self.vector_manager.get_relevant_tables_by_vector(question_vector)

        # Filter to only include tables that actually exist in the DB (Optimized with cache)
        all_tables = self.db_manager.get_usable_table_names()
        relevant_tables = [t for t in relevant_tables if t in all_tables]

        print(f"RAG retrieved relevant tables (filtered): {relevant_tables}")

        # Create/Get executor for this session and this specific query (due to dynamic tables)
        agent_executor = self._create_agent_executor(session_id, include_tables=relevant_tables, extra_context=extra_context)

        full_query = question
        if format_instruction:
            full_query += f"\nFormat output as: {format_instruction}"

        try:
            result = agent_executor.invoke({"input": full_query})

            sql_queries = []
            for step in result.get("intermediate_steps", []):
                if hasattr(step[0], 'tool') and step[0].tool == "sql_db_query":
                    sql_queries.append(step[0].tool_input)

            # Save to vector DB for self-learning (Asynchronous)
            self.vector_manager.add_chat_interaction(question, result["output"], sql_queries, session_id)

            return {
                "answer": answer,
                "sql_queries": sql_queries
            }

        except Exception as e:
            sql_queries = []
            last_observation = None
            if hasattr(e, 'intermediate_steps'):
                for step in e.intermediate_steps:
                    if step[0].tool == "sql_db_query":
                        sql_queries.append(step[0].tool_input)
                        last_observation = step[1]

            try:
                fallback_prompt = (
                    f"The user asked: {full_query}\n"
                    f"Database result found: {last_observation}\n"
                    "Please provide the final answer."
                ) if last_observation else full_query

                if extra_context:
                    fallback_prompt = f"{extra_context}\n\n" + fallback_prompt

                response = self.llm.invoke(fallback_prompt) if hasattr(self.llm, 'invoke') else self.llm(fallback_prompt)
                answer = response.content if hasattr(response, 'content') else str(response)

                # Save successful fallback to vector DB for self-learning (Asynchronous)
                self.vector_manager.add_chat_interaction(question, answer, sql_queries, session_id)

                return {
                    "answer": answer,
                    "sql_queries": sql_queries,
                    "error": str(e)
                }
            except Exception as e2:
                return {
                    "answer": f"Error: {str(e)}",
                    "sql_queries": []
                }
