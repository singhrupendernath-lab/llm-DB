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
            # For smaller models, ReAct is hard.
            # We'll try to use a very structured prompt.
            agent_type = AgentType.ZERO_SHOT_REACT_DESCRIPTION

        # Customizing the prompt
        prefix = (
            f"You are an expert data assistant for a {self.db_manager.db_type} database.\n"
            "You MUST follow the Thought/Action/Action Input/Observation format strictly.\n\n"
            "Format:\n"
            "Thought: I need to check the schema of the tables.\n"
            "Action: sql_db_schema\n"
            "Action Input: table_name1, table_name2\n"
            "Observation: [schema details]\n"
            "... (this can repeat)\n"
            "Thought: I now know the final answer.\n"
            "Final Answer: Your refined and decorated answer here.\n\n"
            "Guidelines:\n"
            f"1. Only use {self.db_manager.db_type} SQL syntax.\n"
            "2. Present the final answer in a refined Markdown format with tables or bullet points.\n"
            "3. If the question is general (like 'Hi' or 'Who are you?'), use 'Final Answer:' immediately.\n"
        )

        self.agent_executor = create_sql_agent(
            llm=self.llm,
            db=self.db,
            verbose=True,
            agent_type=agent_type,
            handle_parsing_errors=True,
            prefix=prefix
        )

    def ask(self, question: str, format_instruction: str = None):
        full_query = question
        if format_instruction:
            full_query += f"\n\nPlease format the output as follows: {format_instruction}"
        
        try:
            result = self.agent_executor.invoke({"input": full_query})
            return result["output"]
        except Exception as e:
            try:
                print(f"Agent failed, falling back to direct LLM: {e}")
                if hasattr(self.llm, 'invoke'):
                    response = self.llm.invoke(full_query)
                    return response.content if hasattr(response, 'content') else str(response)
                else:
                    return str(e)
            except Exception as e2:
                return f"Error occurred: {str(e)} and fallback also failed: {str(e2)}"

    def generate_report(self, report_description: str, format_type: str = "table"):
        prompt = f"Generate a detailed report for: {report_description}. Output format: {format_type}."
        return self.ask(prompt)
