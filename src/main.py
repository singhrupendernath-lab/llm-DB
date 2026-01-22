import sys
from db_manager import DBManager
from llm_manager import LLMManager
from oracle_bot import OracleBot
from config import Config

def main():
    print(f"--- DB-LLM RAG Bot ({Config.DB_TYPE} + {Config.LLM_TYPE}) ---")
    
    # Initialize managers
    db_manager = DBManager(db_type=Config.DB_TYPE, include_tables=Config.INCLUDE_TABLES)
    llm_manager = LLMManager(llm_type=Config.LLM_TYPE)
    
    bot = OracleBot(db_manager, llm_manager)
    
    if len(sys.argv) > 1:
        # One-off query from CLI
        query = " ".join(sys.argv[1:])
        print(f"Querying: {query}")
        result_dict = bot.ask(query)

        if result_dict.get("sql_queries"):
            print("\nExecuted SQL Queries:")
            for sql in result_dict["sql_queries"]:
                print(f"  {sql}")

        print("\nResult:")
        print(result_dict["answer"])
    else:
        # Interactive mode
        print("Enter your queries (type 'exit' to quit):")
        while True:
            try:
                user_input = input("\nUser: ")
                if user_input.lower() in ['exit', 'quit']:
                    break
                
                format_instruction = input("Format instruction (optional, press Enter to skip): ")
                
                print("\nBot: ", end="", flush=True)
                final_answer = ""
                sql_queries = []

                # Use streaming for interactive mode
                for chunk in bot.stream_ask(user_input, format_instruction if format_instruction else None):
                    if chunk["type"] == "final_answer":
                        print(chunk["content"], end="", flush=True)
                        final_answer = chunk["content"]
                    elif chunk["type"] == "action":
                        # We print actions in the background (hidden or minimal)
                        # but if we want it fast, we just stay quiet until final answer
                        pass
                    elif chunk["type"] == "error":
                        print(f"\n[Error] {chunk['content']}")

                print() # New line after answer

                if not final_answer:
                    # Fallback if streaming didn't produce a final answer
                    result_dict = bot.ask(user_input, format_instruction if format_instruction else None)
                    print(result_dict['answer'])
                    if result_dict.get("sql_queries"):
                        print("\n[SQL Queries Executed]")
                        for sql in result_dict["sql_queries"]:
                            print(f"  {sql}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
