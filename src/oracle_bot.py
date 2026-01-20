from langchain_community.agent_toolkits import create_sql_agent
try:
    from langchain.agents.agent_types import AgentType
except ImportError:
    try:
        from langchain_classic.agents.agent_types import AgentType
    except ImportError:
        # Fallback if both fail
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
            # tool-calling is preferred for newer OpenAI models,
            # but openai-functions is very stable.
            agent_type = "tool-calling"
        else:
            agent_type = AgentType.ZERO_SHOT_REACT_DESCRIPTION

        # Customizing the prompt to match user's "decorated details" requirement
        prefix = (
            f"You are an expert data assistant for a {self.db_manager.db_type} database. "
            "Your goal is to provide accurate answers by querying the database and "
            "then refining and decorating the output for the user.\n\n"
            f"When answering questions about data from the {self.db_manager.db_type} database:\n"
            f"1. Generate a syntactically correct {self.db_manager.db_type} SQL query.\n"
            "2. Execute it and analyze the results.\n"
            "3. Present the final answer in a refined, 'decorated' format. Use tables (Markdown tables), "
            "bullet points, or concise summaries to make the data easy to read and professional.\n\n"
            "If the question is NOT about the database (e.g., general greetings or general knowledge), "
            "answer it directly without using SQL tools. For example, if asked 'Who are you?', "
            "explain your role as a database assistant."
        )

        # Initialize the SQL Agent with the custom prefix
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
