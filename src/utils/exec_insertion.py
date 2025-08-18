import sys, glob, json, copy, re, subprocess, concurrent.futures
from termcolor import colored

def replace_values(tool_config, root_dir, vulnerability_name):
    # Replaces 'variables' (dummy values) from injection tools configuration JSON
    # Those 'variables' enable users to instantiate novel injection tools calls
    
    # Add project root directory and vulnerability name to contract's source code location inside container
    tool_config["contracts_src"] = tool_config["contracts_src"].replace("ROOT_DIR", root_dir).replace("VULNERABILITY_NAME", vulnerability_name)
    
    # Add project root directory and vulnerability name to injected contract's output location inside container
    tool_config["output_dir"] = tool_config["output_dir"].replace("ROOT_DIR", root_dir).replace("VULNERABILITY_NAME", vulnerability_name)
    
    # For each listed volume
    for index, string in enumerate(tool_config["volumes"]):
        # Add project root directory and vulnerability name to volume configuration
        tool_config["volumes"][index] = string.replace("ROOT_DIR", root_dir).replace("VULNERABILITY_NAME", vulnerability_name)
    
    # For each listed execution command (which will be run inside the container)
    for index, string in enumerate(tool_config["execution_cmd"]):
        # Add project root directory and vulnerability name to it
        tool_config["execution_cmd"][index] = string.replace("ROOT_DIR", root_dir).replace("VULNERABILITY_NAME", vulnerability_name)

    # Return build command
    return tool_config

def build_command(vulnerability_name, process, cpus, contract, root_dir, tool_config):
    # Name container by its process id
    container_name = f'process{process}'
    
    # Replace JSON configuration "variables" with real values
    renamed_tool_config = replace_values(tool_config, root_dir, vulnerability_name)
    
    volumes_cmd = []
    # Instantiate all required volumes in command
    for volume in renamed_tool_config["volumes"]:
        volumes_cmd.append("-v")
        volumes_cmd.append(volume)

    # Build docker command
    docker_command = [
        "docker", "run",
        "--name", container_name,
        "--cpus", cpus,
        "-v", f"{contract}:{renamed_tool_config["contracts_src"]}"
    ] + volumes_cmd + [
        renamed_tool_config["image"]
    ] + [
        cmd for cmd in renamed_tool_config["execution_cmd"]
    ]

    return docker_command

def load_image(image):
    # List all local Docker images
    result = subprocess.run(
        ['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )

    # Check if the image is in the list
    image_list = result.stdout.splitlines()
    
    # If it is not
    if image not in image_list:
        # Load the required image
        print(f'Loading docker image {image}, may take a while ...')
        subprocess.run(
            ['docker', 'pull', image], 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
            )

def run_container(root_dir, docker_command, tool_config):
    try:
        # Get process characteristics (name and id)
        container_name = docker_command[3]
        process_id = re.findall(r'\d+', docker_command[3])

        # Run injection tool
        subprocess.run(docker_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Create command to copy injected contracts to baked_dataset directory
        copy_command = [
            "docker", "cp",
            f"{container_name}:{tool_config["output_dir"]}", f"{root_dir}/dataset/baked_dataset"
        ]
        # Run copy command
        subprocess.run(copy_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Create command to delete finished docker container
        rm_command = [
            "docker", "container", "rm", f"{container_name}"
        ]
        # Run delete command
        subprocess.run(rm_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return False, f'[i] Finished process{process_id[0]}'
  
    except Exception as e:
        return True, f'[i] An error occurred in process{process_id[0]}: {e}'

# Function for printing iterative report
def move_cursor_up(n):
    sys.stdout.write(f"\033[{n}A")

# Function for printing iterative report
def move_cursor_down(n):
    sys.stdout.write(f"\033[{n}B")

def execute_processes(root_dir, threads, cpus, insertion_tools):
    # Execute concurrent processes via concurrent library
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        # Get contracts to be inserted
        contracts = glob.glob(f'{root_dir}/dataset/raw_dataset/.temp/*')
        
        # Count number of collected contracts
        total_contracts = len(contracts)

        # For each selected insertion tool
        for tool in insertion_tools:
            # Open its execution configuration JSON
            with open(f'{root_dir}/configs/insertion_tools//{tool}/{tool}.json', "r") as json_file:
                # Read file
                tool_config = json.load(json_file)
                
                # Load corresponding docker image
                load_image(tool_config["image"])

                # For each supported vulnerability
                for vulnerability in tool_config["vulnerabilities"]:
                    # Create commands list
                    commands = []
                    
                    # Create tool configuration copy (for safety)
                    tool_config_copy = copy.deepcopy(tool_config)
                    
                    # For each contract
                    for index, contract in enumerate(contracts):
                        # Build command for executing the insertion tool's docker
                        commands.append(build_command(vulnerability, index+1, cpus, contract, root_dir, tool_config_copy))
                    
                    print(f'[+] Executing {colored(tool, 'green')} to insert {colored(vulnerability, 'green')}')

                    # Create a dictionary to keep track of the future objects
                    future_to_command = {executor.submit(run_container, root_dir, command, tool_config_copy): command for command in commands}

                    # Counter of processed files and errors
                    count = 0
                    errors = 0
                    
                    # As each concurrent process ends
                    for future in concurrent.futures.as_completed(future_to_command):
                        # COunt another finished process
                        count = count + 1

                        # Read return status
                        return_status, return_message = future.result()

                        # If there was any error
                        if return_status:
                            # Count error
                            errors = errors + 1
                            
                            # Inform the user something went wrong
                            move_cursor_down(errors)
                            print(f'{colored(return_message, 'red')}', end='\r', flush=True)
                            move_cursor_up(errors)
                        
                        # If no error occurred
                        else:
                            # Print updated processing count
                            print(f'{return_message}: {count}/{total_contracts}', end='\r', flush=True)
                    
                    move_cursor_down(errors+1)

        print(colored('[+] All insertion tasks completed', 'green'))

if __name__ == "__main__":
    # Input variables
    root_dir = sys.argv[1]
    threads = sys.argv[2]
    cpus = sys.argv[3]
    insertion_tools_string = sys.argv[4]
    
    # Get which insertion tools should be executed
    insertion_tools = []
    for tool in insertion_tools_string.split(" "):
        insertion_tools.append(tool)

    # execute insertion process
    execute_processes(root_dir, int(threads), cpus, insertion_tools)  
