import os
import subprocess
import sys

def main():
    print("Starting DB-LLM Frontend (Streamlit)...")
    # Get the directory of this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_path = os.path.join(current_dir, "src", "frontend.py")

    try:
        subprocess.run(["streamlit", "run", frontend_path], check=True)
    except KeyboardInterrupt:
        print("\nFrontend stopped.")
    except Exception as e:
        print(f"Error starting frontend: {e}")

if __name__ == "__main__":
    main()
