from langchain_community.agent_toolkits import create_sql_agent
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
        
        # Determine agent type
        if self.llm_manager.llm_type == "openai":
            agent_type = "tool-calling"
        else:
            agent_type = AgentType.ZERO_SHOT_REACT_DESCRIPTION

        # Highly structured prompt for modern Instruct models (Llama 3, Qwen, Phi-3)
        prefix = (
            f"You are a professional Data Analyst assistant. You have access to a {self.db_manager.db_type} database.\n"
            "Your goal is to provide accurate, decorated, and refined answers based on the database content.\n\n"
            "STRICT RULES:\n"
            "1. ALWAYS use 'sql_db_schema' to understand table structures before querying.\n"
            f"2. Generate syntactically correct {self.db_manager.db_type} SQL queries.\n"
            "3. Present data results in professional Markdown tables or lists.\n"
            "4. For general greetings or role questions, answer directly without tools.\n\n"
            "FORMAT TO FOLLOW:\n"
            "Thought: [Brief reasoning]\n"
            "Action: [Tool Name]\n"
            "Action Input: [Input for the tool]\n"
            "Observation: [Tool result]\n"
            "... (repeat as necessary)\n"
            "Thought: I have the information needed.\n"
            "Final Answer: [Your refined response here]\n\n"
            f"Database Platform: {self.db_manager.db_type}\n"
            "Begin!"
        )

        self.agent_executor = create_sql_agent(
            llm=self.llm,
            db=self.db,
            verbose=True,
            agent_type=agent_type,
            handle_parsing_errors=True,
            prefix=prefix,
            return_intermediate_steps=True
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
                response = self.llm.invoke(full_query)
                answer = response.content if hasattr(response, 'content') else str(response)
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
