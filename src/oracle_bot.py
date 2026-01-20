from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from db_manager import DBManager
from llm_manager import LLMManager

class OracleBot:
    def __init__(self, db_manager: DBManager, llm_manager: LLMManager):
        self.db_manager = db_manager
        self.llm_manager = llm_manager
        self.llm = self.llm_manager.get_llm()
        self.db = self.db_manager.get_db()
        
        # Initialize the SQL Agent
        # We let create_sql_agent choose the best agent type for the LLM
        self.agent_executor = create_sql_agent(
            llm=self.llm,
            db=self.db,
            verbose=True,
            handle_parsing_errors=True
        )

    def ask(self, question: str, format_instruction: str = None):
        full_query = question
        if format_instruction:
            full_query += f"\n\nPlease format the output as follows: {format_instruction}"
        
        # Instruction to handle both DB and general queries
        instruction = (
            "You are a helpful assistant that can query a database to answer questions. "
            "If the question is about the data in the database, use the provided tools to query it. "
            "If the question is NOT about the database or you can answer it with your general knowledge, "
            "just answer it directly. Do not try to query the database for general knowledge questions like 'Who are you?' or 'What is 2+2?'."
        )

        try:
            result = self.agent_executor.invoke({"input": f"{instruction}\nQuestion: {full_query}"})
            return result["output"]
        except Exception as e:
            # Fallback if the agent fails completely
            try:
                print(f"Agent failed, falling back to direct LLM: {e}")
                # Some LLMs might not support invoke directly or might return different objects
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
