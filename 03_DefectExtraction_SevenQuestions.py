"""
This script implements a comprehensive analysis system for extracting and processing RAAC (Reinforced Aerated Autoclaved Concrete) information from PDF documents using the Claude API.

Key Features:
- PDF text extraction and processing with error handling
- AI-powered analysis of RAAC-related information across 7 key categories:
  1. RAAC applications and use cases
  2. Defect types and characteristics
  3. Root causes of defects
  4. Warning signs and indicators
  5. Inspection aspects and elements
  6. Inspection methodologies
  7. Tools and equipment for inspection
- Two-pass analysis system:
  - Initial pass for basic information extraction
  - Secondary pass for deeper analysis and validation
- Chunk-based text processing for handling large documents
- Automatic retry mechanism with exponential backoff
- Comprehensive logging system
- Excel output generation with separate sheets for initial and retry analyses

The script is designed for thorough analysis of RAAC-related documents, with built-in mechanisms to ensure comprehensive coverage and accuracy of the extracted information.
"""

import os
import anthropic
import PyPDF2
import pandas as pd
import logging
import time
from io import StringIO

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Claude client
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("Please set the ANTHROPIC_API_KEY environment variable")
client = anthropic.Anthropic(api_key=api_key)


def extract_text_from_pdf(file_path):
    """
    Extracts text content from a PDF file.

    Args:
        file_path (str): Path to the PDF file to be processed.

    Returns:
        str: Extracted text content from the PDF, or None if extraction fails.

    Note:
        Uses PyPDF2 for text extraction and handles potential errors during the process.
        Logs any errors that occur during extraction.
    """
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = StringIO()
            for page in reader.pages:
                text.write(page.extract_text())
        return text.getvalue()
    except Exception as e:
        logging.error(f"Error extracting text from {file_path}: {e}")
        return None


def get_raac_information(text, is_retry=False, max_retries=3):
    """
    Analyzes text content for RAAC-related information using the Claude API.

    Args:
        text (str): The text content to be analyzed.
        is_retry (bool): Flag indicating if this is a retry attempt for deeper analysis.
        max_retries (int): Maximum number of API call retry attempts.

    Returns:
        str: Structured text containing RAAC information, or None if analysis fails.

    Note:
        Implements exponential backoff for retries.
        Uses different prompts for initial and retry attempts.
        Logs API responses and errors.
    """
    system_content = """You are an expert assistant specializing in extracting and interpreting information about reinforced aerated autoclaved concrete (RAAC). Your task is to analyze the given text and extract relevant information, even if it's not explicitly stated under specific headings."""

    prompt = f"""
    Analyze the following text about reinforced aerated autoclaved concrete (RAAC) and extract information for these categories:

    1. Where RAAC is applied? (e.g., buildings, bridges, etc.)
    2. RAAC defects?
    3. Causes of defects?
    4. Warning signs?
    5. Aspects/elements to inspect?
    6. Inspection methods?
    7. Any tools mentioned to inspect the defects?

    {"If information for a category is not explicitly stated, use your expertise to infer it from the context if possible. If no relevant information can be found or inferred, respond with 'Not mentioned' for that category." if not is_retry else "Please provide more detailed information for each category, even if you need to make reasonable inferences based on the context. If absolutely no information can be inferred, state 'No information available' for that category."}

    Provide your answers in a structured format, with each category clearly labeled and separated by newlines. Do not repeat information within a category.

    Text: {text}
    """

    messages = [{"role": "user", "content": prompt}]

    logging.info(f"Sending message to API for information extraction...")

    retries = 0
    while retries < max_retries:
        try:
            response = client.messages.create(
                model="claude-3-opus-20240229",
                messages=messages,
                system=system_content,
                max_tokens=2000
            )
            logging.info("API Response received")
            if response.content and len(response.content) > 0:
                return response.content[0].text.strip()
        except anthropic.APIError as e:
            logging.error(f"API Error: {str(e)}, retrying... {retries + 1}/{max_retries}")
            retries += 1
            time.sleep(2 ** retries)  # Exponential backoff

    logging.error("Max retries reached. Returning error.")
    return None


def parse_raac_information(text):
    """
    Parses the structured RAAC information text into categorized fields.

    Args:
        text (str): The structured text containing RAAC information.

    Returns:
        list: A list of 7 strings containing parsed information for each category.
              Returns list of "Not mentioned" if input is None or empty.

    Note:
        Categories are:
        1. RAAC applications
        2. RAAC defects
        3. Causes of defects
        4. Warning signs
        5. Inspection aspects
        6. Inspection methods
        7. Tools mentioned
    """
    if text is None or len(text.strip()) == 0:
        return ["Not mentioned"] * 7

    categories = [
        "1. Where RAAC is applied?",
        "2. RAAC defects?",
        "3. Causes of defects?",
        "4. Warning signs?",
        "5. Aspects/elements to inspect?",
        "6. Inspection methods?",
        "7. Any tools mentioned to inspect the defects?"
    ]

    fields = [""] * 7
    current_category = -1

    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue

        category_match = next((i for i, cat in enumerate(categories) if line.startswith(cat)), None)
        if category_match is not None:
            current_category = category_match
        elif current_category != -1:
            fields[current_category] += line + " "

    # Clean up fields
    fields = [field.strip() if field else "Not mentioned" for field in fields]

    logging.info(f"Parsed information: {fields}")
    return fields


def process_text_in_chunks(text, chunk_size=15000, is_retry=False):
    """
    Processes large text content in chunks to handle API token limits.

    Args:
        text (str): The text content to be processed.
        chunk_size (int): Maximum size of each text chunk.
        is_retry (bool): Flag indicating if this is a retry attempt.

    Returns:
        list: Combined information from all chunks, with duplicates removed.

    Note:
        Splits text into manageable chunks, processes each chunk separately,
        and combines the results while removing duplicates.
    """
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    all_information = []

    for chunk in chunks:
        raw_information = get_raac_information(chunk, is_retry)
        parsed_information = parse_raac_information(raw_information)
        all_information.append(parsed_information)

    # Combine information from all chunks
    combined_information = []
    for i in range(7):
        combined = ". ".join(
            set([info[i] for info in all_information if info[i] not in ["Not mentioned", "No information available"]]))
        combined_information.append(combined if combined else "Not mentioned")

    return combined_information


def should_retry(parsed_information):
    """
    Determines if a retry analysis is needed based on the completeness of information.

    Args:
        parsed_information (list): List of parsed information for each category.

    Returns:
        bool: True if more than half of the categories are "Not mentioned", False otherwise.

    Note:
        Used to decide whether to perform a deeper analysis of the text.
    """
    # Check if more than half of the categories are "Not mentioned"
    not_mentioned_count = sum(1 for info in parsed_information if info == "Not mentioned")
    return not_mentioned_count > 3


def process_pdfs(folder_path):
    """
    Processes all PDF files in the specified folder for RAAC information.

    Args:
        folder_path (str): Path to the folder containing PDF files to process.

    Note:
        For each PDF:
        1. Extracts text content
        2. Performs initial analysis
        3. Performs retry analysis if needed
        4. Saves results to Excel file
        Includes comprehensive error handling and logging.
    """
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]

    for filename in pdf_files:
        file_path = os.path.join(folder_path, filename)
        logging.info(f"Processing: {filename}")

        try:
            text = extract_text_from_pdf(file_path)
            if text:
                # First pass
                parsed_information = process_text_in_chunks(text)

                # Second pass (retry)
                logging.info(f"Performing second pass for {filename}")
                retry_information = process_text_in_chunks(text, is_retry=True)

                data = {
                    "filename": [filename, filename],
                    "Where RAAC applied?": [parsed_information[0], retry_information[0]],
                    "RAAC defects?": [parsed_information[1], retry_information[1]],
                    "Causes of defects?": [parsed_information[2], retry_information[2]],
                    "Warning signs?": [parsed_information[3], retry_information[3]],
                    "Aspects/Elements to inspect?": [parsed_information[4], retry_information[4]],
                    "Inspection methods?": [parsed_information[5], retry_information[5]],
                    "Tools mentioned?": [parsed_information[6], retry_information[6]]
                }

                df = pd.DataFrame(data)
                output_path = os.path.join(folder_path, f"{os.path.splitext(filename)[0]}_RAAC_info.xlsx")

                try:
                    df.to_excel(output_path, index=False)
                    logging.info(f"Results saved to {output_path} for {filename}")
                except Exception as e:
                    logging.error(f"Error saving Excel file: {e}")

            else:
                logging.warning(f"No text extracted from {filename}")

        except Exception as e:
            logging.error(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    folder_path = "/Users/lixuliu/Desktop/Paper 1-Critical Evaluation of Methods for RAAC Defect Recognition/SEP_RAAC_Search_02_ reinforced AND aerated AND autoclaved AND concrete/Stage4_Analyse_ExtractInformation/RAAC_mentions_rechecked_processed_YN_allpaperselected"
    process_pdfs(folder_path)