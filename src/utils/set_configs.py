import json, sys, glob
from termcolor import colored

def huanggai_config(root_dir, timeout):
    try:
        # Get configuration files directories
        config_files = glob.glob(f'{root_dir}/configs/huanggai/threads/*/*.json')
        
        # Each configuration file corresponds to one of the 20 supported vulnerabilities
        # For each configuration files
        for file in config_files:
            # Read file and add the configurations
            with open(file, 'r') as read_file:
                data = json.load(read_file)
                vulnerabilityName = file.split("/")[-2] # Read the specific vulnerability
                data[vulnerabilityName][1] = timeout # Set the required timeout

            # Write modifications back to the configuration file
            with open(file, 'w') as write_file:
                json.dump(data, write_file, indent=4)
            
    except Exception as e:
        print(colored(f"An error occurred while setting configurations: {e}", "red"))   
        
if __name__ == "__main__":
    # Input variables
    root_dir = sys.argv[1]
    huanggai_timeout = float(sys.argv[2])

    # Configure Huanggai
    huanggai_config(root_dir, huanggai_timeout)
