import sys
from src.db_manager import DBManager
from src.llm_manager import LLMManager
from src.oracle_bot import OracleBot
from src.config import Config

def main():
    print("--- Oracle-Llama RAG Bot ---")
    
    # Initialize managers
    db_manager = DBManager(use_sqlite=Config.USE_SQLITE, sqlite_path=Config.SQLITE_PATH)
    llm_manager = LLMManager(model_name=Config.LLM_MODEL)
    
    bot = OracleBot(db_manager, llm_manager)
    
    if len(sys.argv) > 1:
        # One-off query from CLI
        query = " ".join(sys.argv[1:])
        print(f"Querying: {query}")
        result = bot.ask(query)
        print("\nResult:")
        print(result)
    else:
        # Interactive mode
        print("Enter your queries (type 'exit' to quit):")
        while True:
            try:
                user_input = input("\nUser: ")
                if user_input.lower() in ['exit', 'quit']:
                    break
                
                format_instruction = input("Format instruction (optional, press Enter to skip): ")
                
                result = bot.ask(user_input, format_instruction if format_instruction else None)
                print(f"\nBot: {result}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
