import tkinter as tk
from tkinter import filedialog
import requests
import json
import uvicorn
import threading
import time
import os
import sys

# --- Pre-run check for project structure ---
def check_project_structure():
    """Checks for the existence of required __init__.py files."""
    print("--- Checking Project Structure ---")
    paths_to_check = ["api", "core", "schemas"]
    all_good = True
    for path in paths_to_check:
        init_file = os.path.join(path, "__init__.py")
        if not os.path.exists(init_file):
            print(f"ERROR: Missing file '{init_file}'.")
            print(f"Please create an empty file at this location for the application to work.")
            all_good = False
    if not all_good:
        print("------------------------------------")
        sys.exit("Project structure is incorrect. Please fix the missing files.")
    print("Project structure looks good.")
    print("------------------------------------\n")

# These imports must come after the structure check.
from core.extractor import extract_data_from_pdf
from api.main import app as fastapi_app

def run_fastapi():
    """Runs the FastAPI server in a quiet mode."""
    print("Starting FastAPI server on http://127.0.0.1:8000")
    uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="warning")

def main():
    """Main function to run the PDF extraction and conversion process."""
    # Start FastAPI in a separate thread
    fastapi_thread = threading.Thread(target=run_fastapi)
    fastapi_thread.daemon = True
    fastapi_thread.start()
    time.sleep(2) # Give the server a moment to start

    # --- GUI to select PDF ---
    print("Opening file dialog to select a PDF...")
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    pdf_path = filedialog.askopenfilename(
        title="Select a PDF file",
        filetypes=(("PDF files", "*.pdf"), ("All files", "*.*"))
    )

    if not pdf_path:
        print("No file selected. Exiting.")
        return

    print(f"Selected file: {pdf_path}")

    # --- Extraction and Conversion ---
    try:
        print("\n--- Starting Data Extraction ---")
        extracted_data = extract_data_from_pdf(pdf_path)
        print("--- Extraction complete ---")
        
        print("\n--- Extracted Data (JSON) ---")
        print(json.dumps(extracted_data, indent=2, ensure_ascii=False))
        print("-----------------------------\n")

        print("--- Sending data to API for CSV conversion ---")
        api_url = "http://127.0.0.1:8000/convert-to-csv/"
        response = requests.post(api_url, json=extracted_data)
        response.raise_for_status()  # Raise an exception for bad status codes (like 404 or 500)

        print("API response:", response.json())
        print("--------------------------------------------\n")
        print("✅ Process finished successfully! Check for 'output.csv' in your project folder.")

    except requests.exceptions.RequestException as e:
        print(f"\n--- ERROR ---")
        print(f"An error occurred while calling the API: {e}")
        print("Please ensure the FastAPI server is running correctly.")
        print("---------------")
    except Exception as e:
        print(f"\n--- AN UNEXPECTED ERROR OCCURRED ---")
        print(f"Error: {e}")
        print("--------------------------------------")


if __name__ == "__main__":
    check_project_structure()
    print("Reminder: Ensure Ollama is running. You can start it with the 'ollama serve' command.")
    main()
 