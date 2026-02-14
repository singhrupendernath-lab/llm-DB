from langchain_community.agent_toolkits import create_sql_agent
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
from langchain_community.utilities import SQLDatabase

class OracleBot:
    def __init__(self, db_manager: DBManager, llm_manager: LLMManager):
        self.db_manager = db_manager
        self.llm_manager = llm_manager
        self.llm = self.llm_manager.get_llm()
        self.reports_manager = ReportsManager()
        self.vector_manager = VectorManager(db_manager)

        # Store memories by session_id
        self.memories = {}
        # Store executors by session_id (optional, can also recreate)
        self.executors = {}

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

        # Create a dynamic DB instance with only relevant tables to save tokens
        db = SQLDatabase(self.db_manager.engine, include_tables=include_tables, sample_rows_in_table_info=2)

        # Oracle semicolon fix
        if self.db_manager.db_type == "oracle":
            original_run = db.run
            def wrapped_run(command, *args, **kwargs):
                if isinstance(command, str):
                    command = command.strip().rstrip(';')
                return original_run(command, *args, **kwargs)
            db.run = wrapped_run

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
            verbose=True,
            agent_type=agent_type,
            prefix=prefix,
            suffix=suffix,
            return_intermediate_steps=True,
            max_iterations=30,
            early_stopping_method="generate",
            agent_executor_kwargs={
                "memory": memory,
                "handle_parsing_errors": "Error! Use: Thought, Action, Action Input. STOP after Input."
            }
        )

    def ask(self, question: str, format_instruction: str = None, session_id: str = "default"):
        # Retrieve relevant past interactions for self-learning
        extra_context = self.vector_manager.search_relevant_chat(question)

        # Check for predefined reports first
        report_id = self.reports_manager.find_report_id(question)
        if report_id:
            report = self.reports_manager.get_report(report_id)
            missing = self.reports_manager.get_missing_variables(report_id, question)
            if missing:
                return {
                    "answer": f"The report '{report['name']}' ({report_id}) requires additional information: {', '.join(missing)}. Please provide these details.",
                    "sql_queries": []
                }

            query = self.reports_manager.format_query(report_id, question)
            try:
                # We use the raw engine to execute predefined reports to avoid SQLDatabase overhead
                with self.db_manager.engine.connect() as conn:
                    import sqlalchemy
                    data = conn.execute(sqlalchemy.text(query)).fetchall()

                self.reports_manager.log_execution(report_id, query)

                if not data:
                    return {
                        "answer": "No records found for the requested criteria.",
                        "sql_queries": [query],
                        "report_id": report_id
                    }

                format_prompt = (
                    f"Transform the following database results into a professional Markdown table.\n"
                    f"Data: {data}\n\n"
                    "Rules:\n1. Output ONLY the table.\n2. Do not add intro/outro text."
                )
                if extra_context:
                    format_prompt = f"{extra_context}\n\n" + format_prompt

                if format_instruction:
                    format_prompt += f"\nNote: {format_instruction}"

                response = self.llm.invoke(format_prompt) if hasattr(self.llm, 'invoke') else self.llm(format_prompt)
                answer = response.content if hasattr(response, 'content') else str(response)

                # Add to memory manually for predefined reports
                memory = self._get_memory(session_id)
                memory.save_context({"input": question}, {"output": answer})

                # Save to vector DB for self-learning
                self.vector_manager.add_chat_interaction(question, answer, [query], session_id)

                return {
                    "answer": answer,
                    "sql_queries": [query],
                    "report_id": report_id
                }
            except Exception as e:
                print(f"Error executing predefined report: {e}")

        # RAG: Find relevant tables
        relevant_tables = self.vector_manager.get_relevant_tables(question)

        # Filter to only include tables that actually exist in the DB to avoid errors
        all_tables = self.db_manager.get_db().get_usable_table_names()
        relevant_tables = [t for t in relevant_tables if t in all_tables]

        print(f"RAG retrieved relevant tables (filtered): {relevant_tables}")

        # Create/Get executor for this session and this specific query (due to dynamic tables)
        agent_executor = self._create_agent_executor(session_id, include_tables=relevant_tables, extra_context=extra_context)

        full_query = question
        if format_instruction:
            full_query += f"\n\nPlease format the output as follows: {format_instruction}"
        
        try:
            result = agent_executor.invoke({"input": full_query})
            sql_queries = []
            for step in result.get("intermediate_steps", []):
                if hasattr(step[0], 'tool') and step[0].tool == "sql_db_query":
                    sql_queries.append(step[0].tool_input)

            # Save to vector DB for self-learning
            self.vector_manager.add_chat_interaction(question, result["output"], sql_queries, session_id)

            return {
                "answer": result["output"],
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

                # Save successful fallback to vector DB for self-learning
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
