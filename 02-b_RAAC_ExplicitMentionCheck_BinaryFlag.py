import pandas as pd
import os
import re


def process_raac_mentions(file_path):
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)

        # Check if the required columns exist
        if 'RAAC_mentioned' not in df.columns or 'Rechecked_RAAC_mention' not in df.columns:
            print("Required columns are missing from the file")
            return

        # Function to clean Rechecked_RAAC_mention column
        def clean_rechecked(text):
            if isinstance(text, str):
                # Look for the conclusion at the end of the text
                match = re.search(
                    r'(the (?:correct )?(?:response|answer) is:?|therefore,?\s*\w*\s*response is:?)\s*(\w)',
                    text.lower())
                if match:
                    conclusion = match.group(2).upper()
                    return conclusion if conclusion in ['Y', 'N'] else 'N'
                elif 'explicitly mentions' in text.lower():
                    return 'Y'
            return 'N'  # Default to 'N' if not Y or N found

        # Create Rechecked_RAAC_mention_cleaned column
        df['Rechecked_RAAC_mention_cleaned'] = df['Rechecked_RAAC_mention'].apply(clean_rechecked)

        # Function to create final column
        def create_final(row):
            raac_mentioned = row['RAAC_mentioned'].strip().upper()
            rechecked_cleaned = row['Rechecked_RAAC_mention_cleaned']
            return f"{raac_mentioned}_{rechecked_cleaned}"

        # Create final column
        df['final'] = df.apply(create_final, axis=1)

        # Create the output file path in the same directory as the input file
        output_file = os.path.join(os.path.dirname(file_path), 'RAAC_mentions_rechecked_processed_YN.xlsx')

        # Save to Excel
        df.to_excel(output_file, index=False)

        print(f"Processed file saved as {output_file}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")


# Usage
file_path = '/Users/lixuliu/Desktop/Paper 1-Critical Evaluation of Methods for RAAC Defect Recognition/SEP_Online Sources/RAAC_mentions_rechecked.xlsx'
process_raac_mentions(file_path)