from langchain_experimental.sql import SQLDatabaseChain
from langchain_core.prompts import PromptTemplate
from .db_manager import DBManager
from .llm_manager import LLMManager

class OracleBot:
    def __init__(self, db_manager: DBManager, llm_manager: LLMManager):
        self.db_manager = db_manager
        self.llm_manager = llm_manager
        self.llm = self.llm_manager.get_llm()
        self.db = self.db_manager.get_db()
        
        # Initialize the SQL Database Chain
        self.db_chain = SQLDatabaseChain.from_llm(
            self.llm, 
            self.db, 
            verbose=True, 
            return_intermediate_steps=True
        )

    def ask(self, question: str, format_instruction: str = None):
        full_query = question
        if format_instruction:
            full_query += f"\n\nPlease format the output as follows: {format_instruction}"
        
        try:
            result = self.db_chain.invoke(full_query)
            return result["result"]
        except Exception as e:
            return f"Error occurred: {str(e)}"

    def generate_report(self, report_description: str, format_type: str = "table"):
        prompt = f"Generate a detailed report for: {report_description}. Output format: {format_type}."
        return self.ask(prompt)
