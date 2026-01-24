from langchain_community.agent_toolkits import create_sql_agent
try:
    from langchain.memory import ConversationBufferMemory
except ImportError:
    try:
        from langchain_classic.memory import ConversationBufferMemory
    except ImportError:
        from langchain_community.memory import ConversationBufferMemory

try:
    from langchain.agents.agent_types import AgentType
except ImportError:
    try:
        from langchain_classic.agents.agent_types import AgentType
    except ImportError:
        class AgentType:
            ZERO_SHOT_REACT_DESCRIPTION = "zero-shot-react-description"
            OPENAI_FUNCTIONS = "openai-functions"

from db_manager import DBManager
from llm_manager import LLMManager

class OracleBot:
    def __init__(self, db_manager: DBManager, llm_manager: LLMManager):
        self.db_manager = db_manager
        self.llm_manager = llm_manager
        self.llm = self.llm_manager.get_llm()
        self.db = self.db_manager.get_db()
        
        # Initialize Memory
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        # Determine agent type
        if self.llm_manager.llm_type == "openai":
            agent_type = "tool-calling"
        else:
            agent_type = AgentType.ZERO_SHOT_REACT_DESCRIPTION

        # Enhanced prompt with memory and dialect placeholder
        # Note: We do NOT use an f-string for the whole block.
        # This allows create_sql_agent to call .format(dialect=...) correctly.
        # We use {{chat_history}} to escape it during the first format() call.
        prefix = (
            "You are a professional Data Analyst assistant.\n"
            "You are connected to a {dialect} database.\n"
            "Your job is to answer user questions by generating accurate SQL queries "
            "and presenting results professionally.\n\n"

            "CURRENT CONVERSATION HISTORY:\n"
            "{{chat_history}}\n\n"

            "IMPORTANT OPERATING RULES:\n"
            "1. At the beginning of the conversation, ALWAYS inspect the database schema first using:\n"
            "   - `sql_db_list_tables`\n"
            "   - `sql_db_schema`\n\n"

            "2. Once you fetch the available table names and column structures, "
            "REMEMBER them for the rest of the conversation.\n"
            "   - Do NOT call schema tools again unless the user asks about a new table.\n"
            "   - Use the remembered schema information to generate future queries faster.\n\n"

            "3. Generate correct, efficient {dialect} SQL queries based on the known schema.\n"

            "4. Always execute queries using `sql_db_query` before answering.\n"

            "5. Present query results in clean Markdown tables or clear bullet summaries.\n"

            "6. If the user asks a general greeting or non-database question, respond directly.\n"

            "7. Never guess table or column names — always rely on schema fetched earlier.\n\n"

            "Database Dialect: {dialect}\n"
            "Begin!\n"
        )


        self.agent_executor = create_sql_agent(
            llm=self.llm,
            db=self.db,
            verbose=True,
            agent_type=agent_type,
            handle_parsing_errors=True,
            prefix=prefix,
            return_intermediate_steps=True,
            agent_executor_kwargs={"memory": self.memory}
        )

    def ask(self, question: str, format_instruction: str = None):
        full_query = question
        if format_instruction:
            full_query += f"\n\nPlease format the output as follows: {format_instruction}"
        
        try:
            result = self.agent_executor.invoke({"input": full_query})

            sql_queries = []
            for step in result.get("intermediate_steps", []):
                if hasattr(step[0], 'tool') and step[0].tool == "sql_db_query":
                    sql_queries.append(step[0].tool_input)

            return {
                "answer": result["output"],
                "sql_queries": sql_queries
            }
        except Exception as e:
            try:
                print(f"Agent failed, falling back to direct LLM: {e}")
                if hasattr(self.llm, 'invoke'):
                    response = self.llm.invoke(full_query)
                    answer = response.content if hasattr(response, 'content') else str(response)
                else:
                    answer = self.llm(full_query)

                return {
                    "answer": answer,
                    "sql_queries": [],
                    "error": str(e)
                }
            except Exception as e2:
                return {
                    "answer": f"Error occurred: {str(e)} and fallback also failed: {str(e2)}",
                    "sql_queries": []
                }

    def generate_report(self, report_description: str, format_type: str = "table"):
        prompt = f"Generate a detailed report for: {report_description}. Output format: {format_type}."
        return self.ask(prompt)
