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

from .db_manager import DBManager
from .llm_manager import LLMManager

class OracleBot:
    def __init__(self, db_manager: DBManager, llm_manager: LLMManager):
        self.db_manager = db_manager
        self.llm_manager = llm_manager
        self.llm = self.llm_manager.get_llm()
        self.db = self.db_manager.get_db()
        
        # Determine agent type based on LLM type
        if self.llm_manager.llm_type == "openai":
            agent_type = "tool-calling"
        else:
            agent_type = AgentType.ZERO_SHOT_REACT_DESCRIPTION

        # Customizing the prompt
        prefix = (
            f"You are an expert data assistant for a {self.db_manager.db_type} database.\n"
            "You MUST use the following format strictly:\n"
            "Thought: I need to query the database to answer the question.\n"
            "Action: sql_db_schema\n"
            "Action Input: [table_names]\n"
            "Observation: [schema results]\n"
            "... (repeat if needed)\n"
            "Thought: I have the information needed.\n"
            "Final Answer: [Your decorated and refined answer]\n\n"
            f"Database Type: {self.db_manager.db_type}\n"
            "Only answer general questions if they don't require database access. "
            "Always try to provide the final answer in a Markdown table for data results."
        )

        self.agent_executor = create_sql_agent(
            llm=self.llm,
            db=self.db,
            verbose=True,
            agent_type=agent_type,
            handle_parsing_errors=True,
            prefix=prefix,
            return_intermediate_steps=True # Enable capturing intermediate steps
        )

    def ask(self, question: str, format_instruction: str = None):
        full_query = question
        if format_instruction:
            full_query += f"\n\nPlease format the output as follows: {format_instruction}"
        
        try:
            result = self.agent_executor.invoke({"input": full_query})

            # Extract SQL queries from intermediate steps
            sql_queries = []
            for step in result.get("intermediate_steps", []):
                action = step[0]
                if action.tool == "sql_db_query":
                    sql_queries.append(action.tool_input)

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
