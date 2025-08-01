from fastapi import FastAPI
from schemas.user_data import UserData
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PDF Data Extractor API",
    description="An API to convert extracted PDF data to CSV.",
    version="1.0.0"
)

@app.post("/convert-to-csv/")
async def convert_to_csv(data: UserData):
    """
    Receives user data in JSON format and converts it to a CSV file.
    """
    try:
        logger.info("Received data for CSV conversion.")
        # Convert the Pydantic model to a dictionary
        data_dict = data.dict(by_alias=True)
        
        # Create a pandas DataFrame
        df = pd.DataFrame([data_dict])
        
        # Define the output path for the CSV
        output_path = "output.csv"
        
        # Save the DataFrame to a CSV file
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        logger.info(f"Data successfully saved to {output_path}")
        return {"message": "CSV file created successfully!", "file_path": output_path}
    except Exception as e:
        logger.error(f"An error occurred during CSV conversion: {e}")
        return {"error": str(e)}

