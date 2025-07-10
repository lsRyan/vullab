import sys, glob, json, csv
from termcolor import colored

def read_sarif(sarif_file, root_dir):
    try:
        vuls_detected = []
        
        with open(sarif_file, "r") as sarif, open(f'{root_dir}/configs/detection_mapping.json') as mapping:
            sarif_data = json.load(sarif)
            sarif_results = sarif_data["runs"][0]["results"]
            SCWE_mapping = json.load(mapping)

            for entry in sarif_results:
                start_line, end_line = vul_lines(entry)
                tool_name = sarif_file.split("/")[-5]
                
                if tool_name.startswith("gpt-") or (tool_name[0] == 'o' and tool_name[1].isdigit() and tool_name[2] == '-'):
                    rule_id = vul_id(entry, sarif_data["runs"][0]["tool"], sarif_file)
                else:
                    rule_id = SCWE_mapping.get(vul_id(entry, sarif_data["runs"][0]["tool"], sarif_file), None)
                
                if rule_id is not None:
                    contract_path = f'{root_dir}/dataset/{sarif_file.split("/")[-4]}/{sarif_file.split("/")[-3]}/smart_contracts/{sarif_file.split("/")[-2]}'
                    vuls_detected.append([tool_name, contract_path, start_line, end_line, rule_id])

        return(vuls_detected)

    except Exception as e:
        print(colored(f"An error occurred while generating the sarif results: {e}", "red"))            

def vul_lines(entry):
    location = entry["locations"][0]["physicalLocation"]
    # Process only if "region" exists
    if "region" in location:
        start_line = location["region"]["startLine"]

        if "endLine" in location["region"]:
            end_line = location["region"]["endLine"]
        else:
            end_line = start_line
    
        return(start_line, end_line)
    return(0, 0)

def vul_id(entry, tools_ids, file_log):
    for id in tools_ids["driver"]["rules"]:
        if entry["ruleId"] == id["id"]:
            return(id["name"])
    
    # If no ID found in tool's ID list
    raise Exception(colored(f'Vulnerability ID not set for file: {file_log}', "red"))

def write_csv(list):
    with open('results/summary.csv', mode="w") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(list)

if __name__ == "__main__":
    root_dir = sys.argv[1]
    sarif_files = glob.glob(f'{root_dir}/results/*/*/*/*/result.sarif')
    tool_reports = [['Tool Name', 'Contract', 'Start Line', 'End Line', 'Vulnerability Name']]
    
    print("[+] Consolidating detected vulnerabilities")
    for sarif_file in sarif_files:
        results = read_sarif(sarif_file, root_dir)
        if results:
            for entry in results:
                tool_reports.append(entry)

    write_csv(tool_reports)
    print(colored(f"[+] Detection report created in {root_dir}/results/summary.csv", "green"))
