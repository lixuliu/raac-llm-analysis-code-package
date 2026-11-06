"""
This script combines multiple Excel files containing RAAC (Reinforced Aerated Autoclaved Concrete) defect data into a single consolidated file.
It merges data from all .xlsx files in a specified directory into one comprehensive dataset.

Key features:
- Automatic detection of all Excel files in directory
- Error handling for corrupt or unreadable files
- Preservation of all data columns
- Simple and efficient merging process
- Direct output to a single Excel file

Process Flow:
1. Scans specified directory for .xlsx files
2. Reads each Excel file using pandas
3. Combines all data into a single DataFrame
4. Handles errors for corrupt or unreadable files
5. Saves combined data to a new Excel file

Error Handling:
- Skips files that cannot be read
- Reports errors for problematic files
- Validates combined data before saving
- Prevents creation of empty output files

Output:
- Creates 'combined_output.xlsx' in the input directory
- Maintains all original columns and data
- Preserves data integrity across files

The script creates a unified dataset from multiple Excel files for easier analysis and reference.
"""

import os
import pandas as pd
import glob

# Define the folder containing the .xlsx files and the output file
input_folder = '/Users/lixuliu/Desktop/Paper 1-Critical Evaluation of Methods for RAAC Defect Recognition/SEP_Online Sources/defects'
output_file = os.path.join(input_folder, 'combined_output.xlsx')

# Use glob to find all xlsx files in the input folder
xlsx_files = glob.glob(os.path.join(input_folder, "*.xlsx"))

# Create an empty DataFrame to store all the data
combined_df = pd.DataFrame()

# Loop through each file and append its data to the combined DataFrame
for file in xlsx_files:
    try:
        # Specify the engine as 'openpyxl'
        df = pd.read_excel(file, engine='openpyxl')
        combined_df = pd.concat([combined_df, df], ignore_index=True)
    except Exception as e:
        # Print error message and skip the file
        print(f"Error reading {file}: {e}")

# Check if combined_df has data to avoid writing an empty file
if not combined_df.empty:
    # Save the combined data to a new Excel file in the same folder
    combined_df.to_excel(output_file, index=False)
    print(f"All data combined and saved to '{output_file}'")
else:
    print("No valid data found to combine.")