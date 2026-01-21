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

        # Enhanced prompt with memory and strict formatting
        prefix = (
            f"You are a professional Data Analyst assistant with memory of the current conversation.\n"
            f"You have access to a {self.db_manager.db_type} database.\n"
            "Your goal is to provide accurate, decorated, and refined answers.\n\n"
            "CURRENT CONVERSATION LOG:\n"
            "{{chat_history}}\n\n"
            "OPERATING INSTRUCTIONS:\n"
            "1. ALWAYS use 'sql_db_schema' to understand table structures before querying.\n"
            f"2. Generate correct {self.db_manager.db_type} SQL queries.\n"
            "3. Present data results in professional Markdown tables or lists.\n"
            "4. For general greetings or role questions, answer directly without tools.\n"
            "5. If a report is requested, provide a detailed analysis and summary of the data.\n\n"
            "FORMAT TO FOLLOW (STRICT):\n"
            "Thought: [Your reasoning for the next step]\n"
            "Action: [Tool Name] (MUST be one of: sql_db_query, sql_db_schema, sql_db_list_tables, sql_db_query_checker)\n"
            "Action Input: [The exact input for the tool]\n"
            "Observation: [The result of the tool - this will be provided to you]\n"
            "... (repeat as necessary)\n"
            "Thought: I have the information needed.\n"
            "Final Answer: [Your refined response here]\n\n"
            f"Database Platform: {self.db_manager.db_type}\n"
            "Begin!"
        )

        self.agent_executor = create_sql_agent(
            llm=self.llm,
            db=self.db,
            verbose=False,
            agent_type=agent_type,
            handle_parsing_errors=True,
            prefix=prefix,
            return_intermediate_steps=True,
            agent_executor_kwargs={"memory": self.memory},
            input_variables=["input", "agent_scratchpad", "chat_history"]
        )

    def _correct_spelling(self, text: str) -> str:
        """Corrects spelling and grammar using the LLM."""
        if not text or len(text) < 3:
            return text

        # Strict prompt for spelling correction
        prompt = (
            "System: You are a spelling and grammar correction assistant. "
            "Your task is to take the user's input and provide a corrected version of it. "
            "Do not add any explanations, do not answer questions, and do not provide any meta-commentary. "
            "Only return the corrected text.\n\n"
            f"User Input: {text}\n"
            "Corrected Text:"
        )

        try:
            if hasattr(self.llm, 'invoke'):
                # Try to use a small max_tokens if supported by the LLM object to prevent runaway generation
                # LlamaCpp and ChatOpenAI usually support some way to pass params,
                # but direct invoke might just take the prompt.
                response = self.llm.invoke(prompt)
                corrected = response.content if hasattr(response, 'content') else str(response)
            else:
                corrected = self.llm(prompt)

            # Post-processing to remove common unwanted artifacts
            corrected = corrected.strip()

            # Remove repeated "Corrected Text:" if LLM included it
            prefixes_to_remove = ["Corrected Text:", "Corrected:", "Output:"]
            for p in prefixes_to_remove:
                if corrected.startswith(p):
                    corrected = corrected[len(p):].strip()

            # Strip quotes
            corrected = corrected.strip().strip('"').strip("'")

            # If the LLM returned multiple lines (meta-commentary often follows on new lines),
            # take only the first non-empty line
            lines = [l.strip() for l in corrected.split('\n') if l.strip()]
            if lines:
                corrected = lines[0]

            return corrected
        except Exception as e:
            print(f"Spelling correction failed: {e}")
            return text

    def ask(self, question: str, format_instruction: str = None):
        # Step 1: Correct spelling
        corrected_question = self._correct_spelling(question)

        full_query = corrected_question
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
