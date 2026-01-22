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
            "You are a Strict Database Reporting Specialist. Your sole purpose is to extract data and generate reports.\n"
            f"You have access to a {self.db_manager.db_type} database.\n"
            "Your goal is to provide accurate, data-driven, and concise answers.\n\n"
            "CURRENT CONVERSATION LOG:\n"
            "{{chat_history}}\n\n"
            "OPERATING INSTRUCTIONS:\n"
            "1. SECURITY: ONLY SELECT queries are permitted. You are FORBIDDEN from executing any data modification commands (INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, etc.).\n"
            "2. ALWAYS use 'sql_db_schema' to understand table structures before querying.\n"
            f"3. Generate correct {self.db_manager.db_type} SQL queries for data extraction.\n"
            "4. Present data results in professional Markdown tables or lists.\n"
            "5. Be concise and to the point. Focus strictly on the data and reports requested.\n"
            "6. If a report is requested, provide a detailed analysis and summary of the extracted data.\n\n"
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

    def ask(self, question: str, format_instruction: str = None):
        full_query = question
        if format_instruction:
            full_query += f"\n\nPlease format the output as follows: {format_instruction}"
        
        try:
            # We use invoke here for synchronous results, but main.py can use a generator if needed
            result = self.agent_executor.invoke({"input": full_query})

            sql_queries = []
            for step in result.get("intermediate_steps", []):
                # LangChain intermediate steps are (AgentAction, Observation)
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

    def stream_ask(self, question: str, format_instruction: str = None):
        """Streams the agent's progress and final answer."""
        full_query = question
        if format_instruction:
            full_query += f"\n\nPlease format the output as follows: {format_instruction}"

        try:
            for chunk in self.agent_executor.stream({"input": full_query}):
                # Handle different types of chunks
                if "actions" in chunk:
                    for action in chunk["actions"]:
                        yield {"type": "action", "content": action.log}
                elif "steps" in chunk:
                    for step in chunk["steps"]:
                        yield {"type": "observation", "content": f"Observation: {step.observation}"}
                elif "output" in chunk:
                    yield {"type": "final_answer", "content": chunk["output"]}
        except Exception as e:
            yield {"type": "error", "content": str(e)}

    def generate_report(self, report_description: str, format_type: str = "table"):
        prompt = f"Generate a detailed report for: {report_description}. Output format: {format_type}."
        return self.ask(prompt)
