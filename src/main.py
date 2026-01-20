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
                
                result_dict = bot.ask(user_input, format_instruction if format_instruction else None)

                if result_dict.get("sql_queries"):
                    print("\n[SQL Queries Executed]")
                    for sql in result_dict["sql_queries"]:
                        print(f"  {sql}")

                print(f"\nBot: {result_dict['answer']}")

                if "error" in result_dict:
                    print(f"(Note: An internal error occurred but fallback was used: {result_dict['error']})")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
