import csv, sys, json, glob, re
import pandas as pd
from pathlib import Path

def get_SCWE_id(value):
    # Define SCWE or SCWEX pattern
    SCWE_pattern = r'^\((SCWE|SCWEX)-\d{3}\)'
    
    # Match string with pattern
    match = re.match(SCWE_pattern, value)
    
    # Return match
    return match.group(0)

def is_SCWE(value):
    # Define SCWE or SCWEX pattern
    name_pattern = r'^\((SCWE|SCWEX)-\d{3}\)\s.*'
    
    # Return if the string includes such pattern
    return bool(re.match(name_pattern, value))

def is_hexadecimal(value):
    # Regular expression pattern for a hexadecimal number
    hex_pattern = re.compile(r'^0x[0-9a-fA-F]+$')
    
    # Return if string is an hexadecimal number
    return bool(hex_pattern.match(value))

def rename_dir(dir_path, SCWE_mapping):
    dir_parent = dir_path.parent
    dir_name = str(dir_path.name)

    if not is_SCWE(dir_name):
        new_name = get_SCWE_id(SCWE_mapping[dir_name]) + "_" + dir_name
        dir_path.rename(dir_parent / new_name)

# Renaming csv file (Huanggai labels)
def rename_txt(file_path, SCWE_mapping):
    # Get label directory and name
    parent_dir = file_path.parent
    label_name = str(file_path.stem)
    
    # If the name is not in pure hexadecimal form
    if not is_hexadecimal(label_name):
        # Split file based on '_' character
        label_name = label_name.split('_')
        
        # Huanggai labels are standardized as <address>_<vulnerability name>.txt
        # Concatenate the second part of the split with the .csv extension       
        new_name = Path(label_name[0] + ".csv")
        
        # Read Huanggai's .txt label
        with open(file_path, 'r+') as file:
            # Create a csv data structure following Solidifi standard
            csv_data = [['loc', 'length', 'bug type', 'approach']]
            
            # For each line in HUanggai's label
            for line in file:
                # Huanggai's labels are standardized as <vulnerability name> <vulnerability start line>
                # Get vulnerability name and location
                label_name = SCWE_mapping.get(str(parent_dir).split("/")[-2], label_name)
                label_line = int(line.rstrip().split(": ")[1])
                
                # Append read data into csv format. Standardized all detections as starting and ending in the same line
                csv_data.append([label_line, 1, label_name, 'code snippet injection'])
    
            # Write csv
            with open(parent_dir / new_name, 'w+') as csvfile:
                # Create a csv.writer object
                writer = csv.writer(csvfile)
                # Write data to the CSV file
                writer.writerows(csv_data)
                
        # Delete .txt label
        file_path.unlink()


# Renaming csv file (SolidiFI labels)
def rename_csv(file_path, SCWE_mapping):
    # Get label directory and name
    parent_dir = file_path.parent
    label_name = str(file_path.stem)
    
    # If the name is not in pure hexadecimal form
    if not is_hexadecimal(label_name):
        # Split file based on '_' character
        label_name = label_name.split('_')

        # Solidifi labels are standardized as buggy_<address>.csv
        # Concatenate the second part of the split with the .csv extension
        new_name = Path(label_name[1] + ".csv")

        # Rename file
        file_path.rename(parent_dir / new_name)
        file_path = parent_dir / new_name

    # Open renamed file
    csv_data = pd.read_csv(file_path)
    
    # Map each entry to SCWE form
    csv_data['bug type'] = csv_data['bug type'].apply(lambda value: SCWE_mapping.get(value, value))
    
    # Write back
    csv_data.to_csv(file_path, index=False)
    
# Renaming contracts (Solidity files: .sol)
def rename_sol(file_path):
    # Get contract directory and name
    parent_dir = file_path.parent
    contract_name = str(file_path.stem)
    
    # If the name is not in pure hexadecimal form
    if not is_hexadecimal(contract_name):
        # Split file based on '_' character
        contract_name = contract_name.split('_')
        
        # If the first part is a pure hexadecimal form
        if is_hexadecimal(contract_name[0]):
            new_name = Path(contract_name[0] + ".sol") # Concatenate it with .sol extension
        
        # If the first part is a pure hexadecimal form
        elif is_hexadecimal(contract_name[1]):
            new_name = Path(contract_name[1] + ".sol") # Concatenate it with .sol extension

        # Rename file to only include the hexadecimal address
        file_path.rename(parent_dir / new_name)


if __name__ == "__main__":
    # Input variables
    root_dir = sys.argv[1]

    # Open SCWE mapping for renaming labels
    SCWE_mapping = dict()
    renaming_maps = glob.glob(f'{root_dir}/configs/insertion_tools/*/mapping.json')
    
    # For each 
    for file in renaming_maps:
        with open(file, 'r') as mapping:
            SCWE_mapping = {**SCWE_mapping, **json.load(mapping)}

    # Assert contracts and labels to the standard
    contracts = glob.glob(f'{root_dir}/dataset/baked_dataset/*/smart_contracts/*.sol')
    labels = glob.glob(f'{root_dir}/dataset/baked_dataset/*/labels/*')
    # Rename contracts to <address>.sol
    for contract in contracts:
        rename_sol(Path(contract))
    
    for label in labels:
        # Change labels from .txt to <address>.csv
        # Modify labels to SCWE
        if label.split('/')[-1].split('.')[1] == 'txt':
            rename_txt(Path(label), SCWE_mapping)
        
        # Rename labels to <address>.csv
        # Modify labels to SCWE
        if label.split('/')[-1].split('.')[1] == 'csv':
            rename_csv(Path(label), SCWE_mapping)

    # Add the SCWE id for each directory
    directories = glob.glob(f'{root_dir}/dataset/baked_dataset/*')
    for directory in directories:
        rename_dir(Path(directory), SCWE_mapping)
