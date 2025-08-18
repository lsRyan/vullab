import sys, glob, json, csv
from termcolor import colored

def read_sarif(sarif_file, root_dir):
    try:
        # Detected vulnerabilities list
        vuls_detected = []
        
        # Open sarif file and SCWE mapping reference
        with open(sarif_file, "r") as sarif, open(f'{root_dir}/configs/detection_mapping.json') as mapping:
            # Read both files
            sarif_data = json.load(sarif)
            sarif_results = sarif_data["runs"][0]["results"]
            SCWE_mapping = json.load(mapping)

            # For each detected vulnerability
            for entry in sarif_results:
                # Get tool name
                tool_name = sarif_file.split("/")[-5]
                
                # Get vulnerability location and tool name
                start_line, end_line = vul_lines(entry)
                
                # If the tool is our GPT analyzer
                if tool_name.startswith("gpt-") or (tool_name[0] == 'o' and tool_name[1].isdigit() and tool_name[2] == '-'):
                    # Read vulnerability name
                    rule_id = vul_id(entry, sarif_data["runs"][0]["tool"], sarif_file)
                
                else: # If not
                    # Read vulnerability name and map it to SCWE + SCWEX. Returns None if no match is found
                    rule_id = SCWE_mapping.get(vul_id(entry, sarif_data["runs"][0]["tool"], sarif_file), None)
                
                # Detected vulnerabilities not included in Huanggai and Solidifi are not mapped
                # Hence, if the vulnerability detected is not empty
                if rule_id is not None:
                    # Get contract path
                    contract_path = f'{root_dir}/dataset/{sarif_file.split("/")[-4]}/{sarif_file.split("/")[-3]}/smart_contracts/{sarif_file.split("/")[-2]}'
                    
                    # Append to the detected vulnerabilities list
                    vuls_detected.append([tool_name, contract_path, start_line, end_line, rule_id])

        return(vuls_detected)

    except Exception as e:
        print(colored(f"An error occurred while generating the sarif results: {e}", "red"))            

def vul_lines(entry):
    # Get 'location' tag from sarif detection
    location = entry["locations"][0]["physicalLocation"]
    
    # Process only if "region" exists inside of the location
    if "region" in location:
        # Get start line
        start_line = location["region"]["startLine"]
        
        # If exists...
        if "endLine" in location["region"]:
            end_line = location["region"]["endLine"] # Get end line
        else:
            end_line = start_line # If it does not exists, assume end line as the same of start line
    
        return(start_line, end_line)
    
    # If no location is specified signal that with '0, 0'
    return(0, 0)

def vul_id(entry, tools_ids, file_log):
    # Get vulnerability name from its id (this is a characteristic of sarif reports)
    for id in tools_ids["driver"]["rules"]:
        if entry["ruleId"] == id["id"]: # If id match
            return(id["name"]) # Return the corresponding name
    
    # If no ID found in tool's ID list
    raise Exception(colored(f'Vulnerability ID not set for file: {file_log}', "red"))

def write_csv(list):
    with open('results/summary.csv', mode="w") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(list)

if __name__ == "__main__":
    # Input variables
    root_dir = sys.argv[1]
    
    # Get all detection reports from analysis tools (sarif files)
    sarif_files = glob.glob(f'{root_dir}/results/*/*/*/*/result.sarif')
    
    # Create CSV columns
    tool_reports = [['Tool Name', 'Contract', 'Start Line', 'End Line', 'Vulnerability Name']]
    
    print("[+] Consolidating detected vulnerabilities")
    # For each report
    for sarif_file in sarif_files:
        # Read the report
        results = read_sarif(sarif_file, root_dir)
        
        # If the report is not empty
        if results:
            # Read each entry and add to the CSV structure
            for entry in results:
                tool_reports.append(entry)

    # Write data to CSV file
    write_csv(tool_reports)

    print(colored(f"[+] Detection report created in {root_dir}/results/summary.csv", "green"))
