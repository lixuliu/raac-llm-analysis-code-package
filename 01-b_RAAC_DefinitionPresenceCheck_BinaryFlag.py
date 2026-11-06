"""
This script processes an Excel file containing RAAC definitions and summaries to verify if each entry contains a proper definition of Reinforced Aerated Autoclaved Concrete (RAAC).
It uses the Claude API to perform intelligent verification of definitions and creates standardized Y/N responses.

Key Features:
- AI-Powered Definition Verification:
  - Uses Claude API for intelligent text analysis
  - Verifies both initial and rechecked definitions
  - Handles complex text patterns
- Data Processing:
  - Processes Excel files incrementally
  - Maintains original data structure
  - Adds standardized Y/N columns
- Error Handling:
  - Implements retry mechanism
  - Uses exponential backoff
  - Handles API failures gracefully
- Output Generation:
  - Creates new Excel file with results
  - Saves progress incrementally
  - Preserves original data

Process Flow:
1. Read input Excel file
2. Process each row:
   - Extract initial definition
   - Extract rechecked definition
   - Verify definitions using Claude
   - Update results
3. Save results incrementally
4. Generate final output file

Data Categories:
- Initial definitions/summaries
- Rechecked definitions/summaries
- Initial RAAC definition verification
- Rechecked RAAC definition verification

The script is designed to standardize the verification of RAAC definitions across multiple documents.
"""

import os
import anthropic
import pandas as pd
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Claude client
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("Please set the ANTHROPIC_API_KEY environment variable")
client = anthropic.Anthropic(api_key=api_key)


# Function to check if the definition of RAAC is present
def check_raac_definition(text, max_retries=3):
    """
    Verifies if the given text contains a definition of RAAC using Claude API.

    Args:
        text (str): The text to be checked for RAAC definition.
        max_retries (int): Maximum number of API retry attempts.

    Returns:
        str: 'Y' if definition is found, 'N' if not found or on error.

    Note:
        Features:
        - Intelligent text analysis
        - Retry mechanism with exponential backoff
        - Token limit handling
        - Error logging
    """
    system_content = "You are a helpful assistant that verifies if the given text contains a definition of RAAC (reinforced aerated autoclaved concrete)."

    messages = [
        {
            "role": "user",
            "content": f"""
            The following text is presented. Please check if it contains the definition of reinforced aerated autoclaved concrete (RAAC). 
            If the definition is present, respond with 'Yes'. If no definition is found, respond with 'No'.
            Text: {text[:15000]}  # Truncate to fit within token limit
            """
        }
    ]

    retries = 0
    while retries < max_retries:
        try:
            response = client.messages.create(
                model="claude-3-opus-20240229",  # Ensure the correct model version is used
                messages=messages,
                system=system_content,
                max_tokens=1000
            )
            # Extract the content of the response
            if response.content and len(response.content) > 0:
                completion_text = response.content[0].text.strip()
                # Return 'Y' for 'Yes' and 'N' for 'No'
                return 'Y' if 'Yes' in completion_text else 'N'

        except anthropic.APIError as e:
            logging.error(f"API Error: {str(e)}, retrying... {retries + 1}/{max_retries}")
            retries += 1
            time.sleep(2 ** retries)  # Exponential backoff

    logging.error("Max retries reached. Returning 'N'.")
    return 'N'  # Default to 'N' if the API call fails

# Function to process and update a single row
def process_single_pdf_row(row, index, output_path, df):
    """
    Processes a single row from the Excel file to verify RAAC definitions.

    Args:
        row (pandas.Series): The row to be processed.
        index (int): Index of the current row.
        output_path (str): Path to save the output Excel file.
        df (pandas.DataFrame): The DataFrame being processed.

    Note:
        Process Steps:
        1. Extract initial and rechecked definitions
        2. Verify definitions using Claude
        3. Update DataFrame with results
        4. Save progress incrementally
    """
    logging.info(f"Processing row {index + 1}...")

    # Extract the text from the 'initial_definition_or_summary' and 'rechecked_definition_or_summary' columns
    initial_definition = row['initial_definition_or_summary']
    rechecked_definition = row['rechecked_definition_or_summary']

    # Check if the definition of RAAC is present in both columns using Claude
    initial_raac_defined = check_raac_definition(initial_definition) if pd.notna(initial_definition) else 'N'
    rechecked_raac_defined = check_raac_definition(rechecked_definition) if pd.notna(rechecked_definition) else 'N'

    # Update the DataFrame with 'Y' or 'N' in two new columns
    df.at[index, 'Initial_RAAC_Defined'] = initial_raac_defined
    df.at[index, 'Rechecked_RAAC_Defined'] = rechecked_raac_defined

    # Save the updated DataFrame to Excel after processing each row
    df.to_excel(output_path, index=False)
    logging.info(f"Results saved to {output_path} after processing row {index + 1}")

# Main process to check and update the RAAC definitions
def check_raac_definitions_in_excel(file_path):
    """
    Main function to process the Excel file and verify RAAC definitions.

    Args:
        file_path (str): Path to the input Excel file.

    Note:
        Features:
        - Incremental processing
        - Progress tracking
        - Error handling
        - Automatic column creation
        - Incremental saving
    """
    # Read the Excel file
    df = pd.read_excel(file_path)

    # Add new columns 'Initial_RAAC_Defined' and 'Rechecked_RAAC_Defined' if they don't exist
    if 'Initial_RAAC_Defined' not in df.columns:
        df['Initial_RAAC_Defined'] = ''
    if 'Rechecked_RAAC_Defined' not in df.columns:
        df['Rechecked_RAAC_Defined'] = ''

    # Define the output path for the updated Excel file
    output_path = file_path.replace(".xlsx", "_YN.xlsx")

    # Process each row one by one and save the results incrementally
    for index, row in df.iterrows():
        process_single_pdf_row(row, index, output_path, df)

    logging.info(f"All rows processed and results saved to {output_path}")


if __name__ == "__main__":
    # Example file path, replace with your own file path
    file_path = "/Users/lixuliu/Desktop/Paper 1-Critical Evaluation of Methods for RAAC Defect Recognition/SEP_RAAC_Search_02_ reinforced AND aerated AND autoclaved AND concrete/Stage3_download articles/rest_articles/RAAC_definitions_or_summaries.xlsx"
    check_raac_definitions_in_excel(file_path)
