from langchain_community.agent_toolkits import create_sql_agent
try:
    from langchain.memory import ConversationBufferWindowMemory
except ImportError:
    try:
        from langchain_classic.memory import ConversationBufferWindowMemory
    except ImportError:
        from langchain_community.memory import ConversationBufferWindowMemory

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
from reports_manager import ReportsManager

class OracleBot:
    def __init__(self, db_manager: DBManager, llm_manager: LLMManager):
        self.db_manager = db_manager
        self.llm_manager = llm_manager
        self.llm = self.llm_manager.get_llm()
        self.db = self.db_manager.get_db()
        self.reports_manager = ReportsManager()

        # Initialize Memory - using Window memory to save context tokens
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=3
        )

        # Determine agent type
        # tool-calling is preferred for OpenAI and ChatHuggingFace (Llama 3.1)
        if self.llm_manager.llm_type in ["openai", "huggingface_api"]:
            agent_type = "tool-calling"
        else:
            agent_type = AgentType.ZERO_SHOT_REACT_DESCRIPTION

        # Get usable table names to include in prompt for faster reasoning
        try:
            table_names_list = self.db.get_usable_table_names()
            table_names_str = ", ".join(table_names_list)
        except Exception:
            table_names_str = "all tables"

        # Minimalist prompt to save context tokens
        prefix = (
            "You are an expert SQL Data Analyst. Available tables: {table_names_str}.\n"
            "Dialect: {dialect}. Top K: {top_k}.\n"
            "History: {{chat_history}}\n\n"
            "RULES:\n"
            "1. Greets? Answer direct.\n"
            "2. DB query? Use 'sql_db_schema' first.\n"
            "3. ONLY use tools below. NO hallucinations.\n"
            "4. STOP after 'Action Input:'.\n"
            "5. NO new questions after 'Final Answer'.\n"
        ).replace("{table_names_str}", table_names_str)

        if agent_type == AgentType.ZERO_SHOT_REACT_DESCRIPTION:
            prefix += (
                "FORMAT:\n"
                "Thought: [reasoning]\n"
                "Action: [tool]\n"
                "Action Input: [input]\n"
                "Observation: [system result]\n"
                "... (repeat if needed)\n"
                "Thought: I have the answer\n"
                "Final Answer: [Markdown answer]\n"
            )

        # Custom suffix to avoid the hardcoded "Thought: I should look at the tables"
        # which often causes looping in modern models like Llama 3.
        # We only apply this to ReAct agents.
        if agent_type == AgentType.ZERO_SHOT_REACT_DESCRIPTION:
            suffix = (
                "Begin!\n\n"
                "Question: {input}\n"
                "{agent_scratchpad}"
            )
        else:
            suffix = None

        # Increase iterations as requested by user
        self.agent_executor = create_sql_agent(
            llm=self.llm,
            db=self.db,
            verbose=True,
            agent_type=agent_type,
            prefix=prefix,
            suffix=suffix,
            return_intermediate_steps=True,
            max_iterations=30,
            early_stopping_method="generate",
            agent_executor_kwargs={
                "memory": self.memory,
                "handle_parsing_errors": "Error! Use: Thought, Action, Action Input. STOP after Input."
            }
        )

    def ask(self, question: str, format_instruction: str = None):
        # Check for predefined reports first
        report_id = self.reports_manager.find_report_id(question)
        if report_id:
            report = self.reports_manager.get_report(report_id)

            # Check for missing variables
            missing = self.reports_manager.get_missing_variables(report_id, question)
            if missing:
                return {
                    "answer": f"The report '{report['name']}' ({report_id}) requires additional information: {', '.join(missing)}. Please provide these details.",
                    "sql_queries": []
                }

            # Use format_query to handle parameters
            query = self.reports_manager.format_query(report_id, question)
            print(f"Detected predefined report {report_id}: {report['name']}")
            print(f"Executing Query: {query}")

            try:
                # Execute specific query directly
                data = self.db.run(query)
                self.reports_manager.log_execution(report_id, query)

                # Strict Python check for empty data to prevent hallucinations
                if not data or data == "[]" or data == "()":
                    return {
                        "answer": "No records found for the requested criteria.",
                        "sql_queries": [query],
                        "report_id": report_id
                    }

                # Minimal prompt for formatting to avoid LLM loops/repetitions
                format_prompt = (
                    f"Transform the following database results into a professional Markdown table.\n"
                    f"Data: {data}\n\n"
                    "Rules:\n"
                    "1. Output ONLY the table.\n"
                    "2. Do not add any introductory or closing text.\n"
                    "3. Do not repeat the table."
                )
                if format_instruction:
                    format_prompt += f"\nNote: {format_instruction}"

                if hasattr(self.llm, 'invoke'):
                    response = self.llm.invoke(format_prompt)
                    answer = response.content if hasattr(response, 'content') else str(response)
                else:
                    answer = self.llm(format_prompt)

                return {
                    "answer": answer,
                    "sql_queries": [query],
                    "report_id": report_id
                }
            except Exception as e:
                print(f"Error executing predefined report: {e}")
                # Fall back to agent if predefined query fails

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
            # Fallback logic: check if we have results in intermediate steps even if it failed at the end
            # This handles cases where the LLM fetched the data but failed to parse the final answer or hit token limit
            sql_queries = []
            last_observation = None

            # If the error object has partial results (some langchain versions do)
            if hasattr(e, 'intermediate_steps'):
                for step in e.intermediate_steps:
                    if step[0].tool == "sql_db_query":
                        sql_queries.append(step[0].tool_input)
                        last_observation = step[1]

            try:
                print(f"Agent failed, falling back to direct LLM: {e}")

                fallback_prompt = full_query
                if last_observation:
                    fallback_prompt = (
                        f"The user asked: {full_query}\n"
                        f"Database result found during execution: {last_observation}\n"
                        "Please provide the final answer based on this database result."
                    )

                if hasattr(self.llm, 'invoke'):
                    response = self.llm.invoke(fallback_prompt)
                    answer = response.content if hasattr(response, 'content') else str(response)
                else:
                    answer = self.llm(fallback_prompt)

                return {
                    "answer": answer,
                    "sql_queries": sql_queries,
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
