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
        
        # Determine agent type based on LLM type
        if self.llm_manager.llm_type == "openai":
            agent_type = "tool-calling"
        else:
            agent_type = AgentType.ZERO_SHOT_REACT_DESCRIPTION

        # Optimized prompt for Instruct models like Phi-3
        prefix = (
            f"You are a professional Data Analyst assistant. You have access to a {self.db_manager.db_type} database.\n"
            "Your job is to answer the user's question by querying the database and providing a refined, decorated response.\n\n"
            "STRICT RULES:\n"
            "1. Use ONLY the tools provided to query the database.\n"
            "2. If you don't know the answer or the database doesn't have the info, say so.\n"
            "3. Format your final answer using Markdown (tables, lists) to make it easy to read.\n"
            "4. For general greetings, answer directly without using any tools.\n\n"
            "You MUST use the following format for database queries:\n"
            "Thought: I should look at the schema of the relevant tables.\n"
            "Action: sql_db_schema\n"
            "Action Input: table_name1, table_name2\n"
            "Observation: [schema output]\n"
            "... (repeat if needed)\n"
            "Thought: I have the data. I will now provide the final answer.\n"
            "Final Answer: [Your decorated result here]\n\n"
            f"Currently working on: {self.db_manager.db_type} database."
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

            # Extract SQL queries from intermediate steps
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
