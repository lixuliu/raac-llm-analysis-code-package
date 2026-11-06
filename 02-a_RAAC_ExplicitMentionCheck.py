"""
This script processes PDF documents to check for mentions of Reinforced Aerated Autoclaved Concrete (RAAC).
It implements a two-step verification process: first using a basic text search, then using the Claude API for intelligent verification.

Key Features:
- PDF Processing:
  - Text extraction from PDF files
  - Multi-page handling
  - Error handling for corrupted files
- Two-Step Verification:
  - Basic text search for "RAAC"
  - AI-powered verification
  - Case-insensitive matching
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
2. Initial RAAC Check:
   - Basic text search
   - Case-insensitive matching
3. AI Verification:
   - Intelligent verification
   - Context-aware checking
4. Results Compilation:
   - Save to Excel/CSV
   - Track progress
   - Handle errors

Data Categories:
- File information
- Initial RAAC mentions
- Rechecked RAAC mentions
- Processing status

The script is designed to systematically verify RAAC mentions across multiple PDF documents.
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

# Function to check if the article mentions RAAC
def check_raac_mention(text):
    """
    Performs initial check for RAAC mentions in text.

    Args:
        text (str): The text content to be checked.

    Returns:
        str: "Y" if RAAC is mentioned, "N" if not.

    Note:
        Features:
        - Case-insensitive search
        - Simple text-based verification
        - Direct string matching
    """
    if "RAAC" in text.upper():  # Convert text to uppercase to perform a case-insensitive search
        return "Y"
    else:
        return "N"

# Function to request revalidation ("try again" scenario) using only the text in the document
def recheck_raac_mention(text, initial_result):
    """
    Performs AI-powered verification of RAAC mentions.

    Args:
        text (str): The text content to be verified.
        initial_result (str): Result from the initial check.

    Returns:
        str: "Y" if RAAC is mentioned, "N" if not, or error message.

    Note:
        Features:
        - AI-powered verification
        - Context-aware checking
        - Token limit handling
        - Error handling
    """
    system_content = "You are a helpful assistant that rechecks results when prompted."

    # Message asking the assistant to recheck and confirm the results, using only the content of the text
    messages = [
        {
            "role": "user",
            "content": f"""
            You previously checked if RAAC is mentioned:

            Initial Response: "{initial_result}"

            Please recheck the text and confirm whether RAAC is explicitly mentioned in the text. 
            Respond with either 'Y' if it mentions RAAC or 'N' if it doesn't, and use only the text from the document.

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

            # Return the rechecked response, ensuring it is "Y" or "N"
            return completion_text

    except anthropic.APIError as e:
        logging.error(f"API Error: {str(e)}")
        return "Error in API call"

# Process a single PDF file
def process_single_pdf(filename, folder_path):
    """
    Processes a single PDF file for RAAC mentions.

    Args:
        filename (str): Name of the PDF file to process.
        folder_path (str): Path to the folder containing the PDF.

    Returns:
        dict: Dictionary containing:
            - file name
            - initial RAAC mention result
            - rechecked RAAC mention result

    Note:
        Process Steps:
        1. Extract text from PDF
        2. Check for RAAC mentions
        3. Verify with AI
        4. Return results
    """
    file_path = os.path.join(folder_path, filename)
    logging.info(f"Processing: {filename}")

    try:
        # Extract text from the current PDF
        text = extract_text_from_pdf(file_path)

        if text:
            # Check if the text mentions RAAC
            raac_mention = check_raac_mention(text)

            # Revalidate the RAAC mention using the AI for confirmation
            rechecked_mention = recheck_raac_mention(text, raac_mention)

            return {
                "file name": filename,
                "RAAC_mentioned": raac_mention,
                "Rechecked_RAAC_mention": rechecked_mention
            }

        else:
            logging.warning(f"No text extracted from {filename}")
            return {"file name": filename, "RAAC_mentioned": "No text extracted", "Rechecked_RAAC_mention": "N/A"}

    except Exception as e:
        logging.error(f"Error processing {filename}: {e}")
        return {"file name": filename, "RAAC_mentioned": "Error in processing", "Rechecked_RAAC_mention": "N/A"}

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
    output_path = os.path.join(folder_path, "RAAC_mentions_rechecked.xlsx")

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
            csv_path = os.path.join(folder_path, "RAAC_mentions_rechecked.csv")
            df.to_csv(csv_path, index=False)
            logging.info(f"Results saved as CSV to {csv_path}")

if __name__ == "__main__":
    # Example folder path, replace with your own folder path
    folder_path = "/Users/lixuliu/Desktop/Paper 1-Critical Evaluation of Methods for RAAC Defect Recognition/SEP_Online Sources"

    # Process all PDFs in the specified folder
    process_pdfs(folder_path)
