"""
This script processes PDF documents to extract and verify definitions of Reinforced Aerated Autoclaved Concrete (RAAC).
It uses a two-step verification process with the Claude API to ensure accurate definition extraction and summarization.

Key Features:
- PDF Processing:
  - Text extraction from PDF files
  - Handles multiple pages
  - Error handling for corrupted files
- Two-Step Verification:
  - Initial definition extraction
  - AI-powered rechecking
  - Direct text-based verification
- Data Management:
  - Incremental processing
  - Progress tracking
  - Resume capability
- Output Generation:
  - Excel/CSV output options
  - Structured data storage
  - Error logging

Process Flow:
1. PDF Text Extraction
2. Initial Definition Check:
   - Extract RAAC definition
   - Generate summary if no definition
3. Definition Rechecking:
   - Verify initial results
   - Extract direct quotes
   - Ensure accuracy
4. Results Compilation:
   - Save to Excel/CSV
   - Track progress
   - Handle errors

Data Categories:
- File information
- Initial definitions/summaries
- Rechecked definitions
- Processing status

The script is designed to systematically extract and verify RAAC definitions from multiple PDF documents.
"""

import os
import anthropic
import PyPDF2
import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Claude client
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("Please set the ANTHROPIC_API_KEY environment variable")
client = anthropic.Anthropic(api_key=api_key)

# Function to extract text from PDF
def extract_text_from_pdf(file_path):
    """
    Extracts text content from a PDF file.

    Args:
        file_path (str): Path to the PDF file to be processed.

    Returns:
        str: Extracted text content from the PDF, or None if extraction fails.

    Note:
        Features:
        - Multi-page text extraction
        - Error handling
        - Logging of extraction issues
        - Handles empty pages
    """
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted
        return text
    except Exception as e:
        logging.error(f"Error extracting text from {file_path}: {e}")
        return None


# Process a single PDF file
def process_single_pdf(filename, folder_path):
    """
    Processes a single PDF file to extract and verify RAAC definitions.

    Args:
        filename (str): Name of the PDF file to process.
        folder_path (str): Path to the folder containing the PDF.

    Returns:
        dict: Dictionary containing:
            - file name
            - initial definition/summary
            - rechecked definition

    Note:
        Process Steps:
        1. Extract text from PDF
        2. Get initial definition
        3. Recheck definition
        4. Return results
    """
    file_path = os.path.join(folder_path, filename)
    logging.info(f"Processing: {filename}")

    try:
        # Extract text from the current PDF
        text = extract_text_from_pdf(file_path)

        if text:
            # Step 1: Get the initial RAAC definition or article summary for the current PDF text
            initial_definition = get_raac_definition(text)
            print(f"Initial Result for {filename}: {initial_definition}")

            # Step 2: Automatically trigger a "try again" prompt for the AI to recheck its results using only the text in the document
            rechecked_definition = recheck_raac_definition(text, initial_definition)
            print(f"Rechecked Result for {filename}: {rechecked_definition}")

            # Return the rechecked definition in case it's more accurate
            return {
                "file name": filename,
                "initial_definition_or_summary": initial_definition,  # Store both the initial and final results
                "rechecked_definition_or_summary": rechecked_definition
            }

        else:
            logging.warning(f"No text extracted from {filename}")
            return {"file name": filename, "definition_or_summary": "No text extracted"}

    except Exception as e:
        logging.error(f"Error processing {filename}: {e}")
        return {"file name": filename, "definition_or_summary": "Error in processing"}


# Function to check if the article presents the definition of RAAC or summarize it
def get_raac_definition(text):
    """
    Extracts initial RAAC definition or generates summary from text.

    Args:
        text (str): The text content to be analyzed.

    Returns:
        str: Extracted definition or summary.

    Note:
        Features:
        - Definition extraction
        - Summary generation
        - Token limit handling
        - API error handling
    """
    system_content = "You are a helpful assistant that checks for the presence of definitions in text documents."

    # Initial message asking for the RAAC definition or summary
    messages = [
        {
            "role": "user",
            "content": f"""
            The following text is from an article related to reinforced aerated autoclaved concrete (RAAC).
            Please check if the article presents what RAAC is. If it does, provide the definition. 
            If no definition is clearly present, summarize what the article talks about instead.

            Text: {text[:15000]}  # Truncate to fit within token limit
            """
        }
    ]

    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",  # Ensure the correct model version is used
            messages=messages,
            system=system_content,
            max_tokens=1000
        )

        # Extract the text from the response
        if response.content and len(response.content) > 0:
            completion_text = response.content[0].text.strip()

            # Return the first response from the AI
            return completion_text

    except anthropic.APIError as e:
        logging.error(f"API Error: {str(e)}")
        return "Error in API call"


# Function to request revalidation ("try again" scenario) using only the text in the document
def recheck_raac_definition(text, initial_result):
    """
    Rechecks and verifies the initial RAAC definition.

    Args:
        text (str): The original text content.
        initial_result (str): The initial definition or summary.

    Returns:
        str: Verified definition or error message.

    Note:
        Features:
        - Direct text verification
        - Quote extraction
        - Accuracy checking
        - Error handling
    """
    system_content = "You are a helpful assistant that rechecks results when prompted."

    # Message asking the assistant to recheck and confirm the results, using only the content of the text
    messages = [
        {
            "role": "user",
            "content": f"""
            You previously provided this response regarding RAAC:

            Initial Response: "{initial_result}"

            Please recheck the text and confirm whether the initial results are accurate or provide an accurate definition of RAAC **directly from the text without using your own words**. Ensure that any definition or explanation comes from the document's exact wording.

            Text: {text[:15000]}  # Truncate to fit within token limit
            """
        }
    ]

    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",  # Ensure the correct model version is used
            messages=messages,
            system=system_content,
            max_tokens=1000
        )

        # Extract the text from the rechecked response
        if response.content and len(response.content) > 0:
            completion_text = response.content[0].text.strip()

            # Return the rechecked response, ensuring the wording is from the document
            return completion_text

    except anthropic.APIError as e:
        logging.error(f"API Error: {str(e)}")
        return "Error in API call"

# Main process to handle multiple PDFs
def process_pdfs(folder_path):
    """
    Main function to process multiple PDF files in a folder.

    Args:
        folder_path (str): Path to the folder containing PDF files.

    Note:
        Features:
        - Incremental processing
        - Progress tracking
        - Resume capability
        - Excel/CSV output
        - Error handling
    """
    output_path = os.path.join(folder_path, "RAAC_definitions_or_summaries.xlsx")

    # Load existing results if the file exists
    results = []
    processed_files = set()  # Use a set for quick lookup of processed files

    if os.path.exists(output_path):
        df_existing = pd.read_excel(output_path)
        results = df_existing.to_dict('records')
        processed_files = set(df_existing['file name'].tolist())  # Track processed files

    # Get list of PDF files
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]

    # Filter out files that are already processed
    pdf_files_to_process = [f for f in pdf_files if f not in processed_files]

    if not pdf_files_to_process:
        logging.info("No new PDF files to process.")
        return

    # Process each PDF file one by one
    for filename in pdf_files_to_process:
        result = process_single_pdf(filename, folder_path)
        results.append(result)

        # Save the results to Excel after processing each file
        df = pd.DataFrame(results)
        try:
            df.to_excel(output_path, index=False)
            logging.info(f"Results saved to {output_path} after processing {filename}")
        except ImportError:
            logging.error("Error: openpyxl is not installed. Please install it manually via 'pip install openpyxl'.")
        except Exception as e:
            logging.error(f"Error saving Excel file: {e}")
            csv_path = os.path.join(folder_path, "RAAC_definitions_or_summaries.csv")
            df.to_csv(csv_path, index=False)
            logging.info(f"Results saved as CSV to {csv_path}")


if __name__ == "__main__":
    # Example folder path, replace with your own folder path
    folder_path = "/Users/lixuliu/Desktop/Paper 1-Critical Evaluation of Methods for RAAC Defect Recognition/SEP_RAAC_Search_02_ reinforced AND aerated AND autoclaved AND concrete/Stage4_Analyse_ExtractInformation/rest_articles"

    # Process all PDFs in the specified folder
    process_pdfs(folder_path)
