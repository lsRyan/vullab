import json, sys, glob
from termcolor import colored

def huanggai_config(root_dir, timeout):
    try:
        config_files = glob.glob(f'{root_dir}/configs/huanggai/threads/*/*.json')
        for file in config_files:
            with open(file, 'r') as read_file:
                data = json.load(read_file)
                vulnerabilityName = file.split("/")[-2]
                data[vulnerabilityName][1] = timeout

            with open(file, 'w') as write_file:
                json.dump(data, write_file, indent=4)
            
    except Exception as e:
        print(colored(f"An error occurred while setting configurations: {e}", "red"))   
        
if __name__ == "__main__":
    root_dir = sys.argv[1]
    huanggai_timeout = float(sys.argv[2])

    huanggai_config(root_dir, huanggai_timeout)
