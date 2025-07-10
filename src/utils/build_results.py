import sys, json, glob
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict
from termcolor import colored
import matplotlib.pyplot as plt

def group_directories_by_SCWE(dirs):
    # Dictionary to hold lists of directories grouped by their code
    grouped_directories = defaultdict(list)

    # Iterate over each directory path and group by code
    for dir in dirs:
        # Extract the base name of the directory
        dir_path = Path(dir)
        code = str(dir_path.name).split("_")[0]

        # Add the directory to the corresponding list in the dictionary
        grouped_directories[code].append(dir_path)

    # Convert defaultdict to a regular dict before returning
    return dict(grouped_directories)

def find_function_bounds(contract_path, start_line, end_line):
    with open(contract_path, 'r') as file:
        lines = file.readlines()

    # Ensure the target line number is within the file's range
    if (start_line < 1 or start_line > len(lines)) or (end_line < 1 or end_line > len(lines)):
        return start_line, end_line

    # Find the start of the function
    line_index = start_line - 1  # Convert to 0-based index
    if lines[line_index].strip().startswith("pragma"):
        return line_index + 1, line_index + 1

    while line_index >= 0:
        if lines[line_index].strip().startswith("function") or lines[line_index].strip().startswith("constructor"):
            function_start = line_index + 1  # Convert back to 1-based index
            break
        line_index -= 1
    else:
        return start_line, end_line
    
    # Find the end of the function
    line_index = function_start - 1  # Reset to target line
    brace_count = 0
    while brace_count == 0:
        brace_count += lines[line_index].count('{')
        line_index += 1
    
    while line_index < len(lines):
        brace_count += lines[line_index].count('{')
        brace_count -= lines[line_index].count('}')
        if brace_count == 0:
            function_end = line_index + 1  # Convert back to 1-based index
            break
        line_index += 1
    else:
        return start_line, end_line

    return function_start, function_end

def evaluate(label, detection, detection_results, match_window):
    try:
        for entry in label.iterrows():
            vul_start = entry[1]['loc']
            vul_end = entry[1]['loc'] + (entry[1]['length'] - 1)
            vul_name = entry[1]['bug type']

            detection_results['total'] += 1

            for detected in detection.iterrows():
                tool_name = detected[1]['Tool Name']
                detected_start = detected[1]['Start Line']
                detected_end = detected[1]['End Line']
                detected_name = detected[1]['Vulnerability Name']

                # If tool is Slither, in some cases the detection points out to the whole function instead of the vulnerability line
                if tool_name == 'slither-0.10.4' and detected_start != detected_end:
                    vul_start_temp, vul_end_temp = find_function_bounds(detected[1]['Contract'], vul_start, vul_end)
                    if vul_start_temp != 0 and vul_end_temp != 0:
                        vul_start = vul_start_temp
                        vul_end = vul_end_temp

                # If the tool did not specify a region
                if detected_start == 0 and detected_end == 0:
                    if detected_name == vul_name:
                        detection_results[tool_name] += 1
                
                # If the tool did specify a region
                else:
                    if detected_start >= vul_start-match_window and detected_end <= vul_end+match_window and detected_name == vul_name:
                        detection_results[tool_name] += 1

        return detection_results
                
    
    except Exception as e:
        print(colored(f"An error occurred while generating the sarif results: {e}", "red"))

def consolidate_results(baked_dict, root_dir):
    consolidated_data = {'baked_dataset': baked_dict}

    # Write to a JSON file
    with open(f'{root_dir}/results/consolidated_results.json', "w") as file:
        json.dump(consolidated_data, file, indent=4)

def plot_results(data, root_dir):
    vulnerabilities = list(sorted(data.keys()))
    tools = [tool for tool in next(iter(data.values())) if tool != "total"]
    detection_percentages = {tool: [] for tool in tools}

    for vul in vulnerabilities:
        total = data[vul]["total"]
        for tool in tools:
            detection_percentage = (data[vul][tool] / total) * 100
            detection_percentages[tool].append(detection_percentage)
    
    x = np.arange(len(vulnerabilities))  # X positions for bars
    width = 0.1  # Width of bars

    fig, ax = plt.subplots(figsize=(8, 6))

    for i, tool in enumerate(tools):
        ax.bar(x + i * width, detection_percentages[tool], width, label=tool)

    # Setting Y-axis values to 0% to 100%
    ax.set_ylim(0, 100)  # Y-axis now always goes from 0 to 100%

    # Add horizontal dotted lines at specified Y-axis values
    for value in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
        ax.axhline(y=value, color='gray', linestyle='--', linewidth=0.8)

    vul_labels = list()
    for vul in vulnerabilities:
        vul_labels.append(vul[1:-1])
    
    # Labels & Formatting
    ax.set_xlabel('Vulnerabilities', fontweight="bold")
    ax.set_ylabel('Detection Percentage (%)', fontweight="bold")
    ax.set_title('Detection Percentage by Tool in Baked Dataset', fontsize=14, fontweight="bold")
    ax.set_xticks(x + width / 2)
    ax.set_yticks(range(0, 101, 10))
    ax.set_xticklabels(vul_labels, rotation=45, ha='right')
    ax.legend()

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Save plot as image in the results directory
    plt.savefig(f'{root_dir}/results/baked_dataset_results.png')

    # Show plot
    plt.show()

if __name__ == "__main__":
    root_dir = sys.argv[1]
    match_window = int(sys.argv[2])
    baked_dir = glob.glob(f'{root_dir}/dataset/baked_dataset/*')

    summary_dir = f'{root_dir}/results/summary.csv'
    summary = pd.read_csv(summary_dir)

    detection_tools = summary.iloc[:, 0].unique()

    print("[+] Building results")
    print("[+] Matching detected vulnerabilities with labels in " + colored("baked dataset", "green"))
    baked_results = dict()
    SCWE_dirs = group_directories_by_SCWE(baked_dir)
    for vul, dirs in SCWE_dirs.items():
        detection_results =  {name: 0 for name in detection_tools}
        detection_results['total'] = 0

        labels = list()
        for dir in dirs:
            for label in glob.glob(f'{dir}/labels/*.csv'):
                labels.append(label)
        
        for label in labels:
            detected_vulnerabilities = summary[summary.iloc[:, 1] == label.replace("labels", "smart_contracts").replace(".csv", ".sol")]
            label_data = pd.read_csv(label)

            detection_results = evaluate(label_data, detected_vulnerabilities, detection_results, match_window)

        baked_results[vul] = detection_results

    consolidate_results(baked_results, root_dir)
    plot_results(baked_results, root_dir)

    print(colored("[+] Building process done", "green"))
