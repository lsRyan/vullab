import sys, glob, json, copy, re, subprocess, concurrent.futures
from termcolor import colored

def replace_values(tool_config, root_dir, vulnerability_name):
    tool_config["contracts_src"] = tool_config["contracts_src"].replace("ROOT_DIR", root_dir).replace("VULNERABILITY_NAME", vulnerability_name)
    tool_config["output_dir"] = tool_config["output_dir"].replace("ROOT_DIR", root_dir).replace("VULNERABILITY_NAME", vulnerability_name)
    for index, string in enumerate(tool_config["volumes"]):
        tool_config["volumes"][index] = string.replace("ROOT_DIR", root_dir).replace("VULNERABILITY_NAME", vulnerability_name)
    for index, string in enumerate(tool_config["execution_cmd"]):
        tool_config["execution_cmd"][index] = string.replace("ROOT_DIR", root_dir).replace("VULNERABILITY_NAME", vulnerability_name)

    return tool_config

def build_command(vulnerability_name, process, cpus, contract, root_dir, tool_config):
    container_name = f'process{process}'
    renamed_tool_config = replace_values(tool_config, root_dir, vulnerability_name)
    
    volumes_cmd = []
    for volume in renamed_tool_config["volumes"]:
        volumes_cmd.append("-v")
        volumes_cmd.append(volume)

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
    if image not in image_list:
        print(f'Loading docker image {image}, may take a while ...')
        subprocess.run(
            ['docker', 'pull', image], 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
            )

def run_container(root_dir, docker_command, tool_config):
    try:
        container_name = docker_command[3]
        process_id = re.findall(r'\d+', docker_command[3])

        subprocess.run(docker_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        copy_command = [
            "docker", "cp",
            f"{container_name}:{tool_config["output_dir"]}", f"{root_dir}/dataset/baked_dataset"
        ]
        subprocess.run(copy_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        copy_command = [
            "docker", "container", "rm", f"{container_name}"
        ]
        subprocess.run(copy_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return False, f'[i] Finished process{process_id[0]}'
  
    except Exception as e:
        return True, f'[i] An error occurred in process{process_id[0]}: {e}'

def move_cursor_up(n):
    sys.stdout.write(f"\033[{n}A")

def move_cursor_down(n):
    sys.stdout.write(f"\033[{n}B")

def execute_processes(root_dir, threads, cpus, insertion_tools):
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        contracts = glob.glob(f'{root_dir}/dataset/raw_dataset/.temp/*')
        total_contracts = len(contracts)

        for tool in insertion_tools:
            with open(f'{root_dir}/configs/insertion_tools//{tool}/{tool}.json', "r") as json_file:
                tool_config = json.load(json_file)
                load_image(tool_config["image"])
                for vulnerability in tool_config["vulnerabilities"]:
                    commands = []
                    tool_config_copy = copy.deepcopy(tool_config)
                    for index, contract in enumerate(contracts):
                        commands.append(build_command(vulnerability, index+1, cpus, contract, root_dir, tool_config_copy))
                    
                    print(f'[+] Executing {colored(tool, 'green')} to insert {colored(vulnerability, 'green')}')

                    # Dictionary to keep track of the future objects
                    future_to_command = {executor.submit(run_container, root_dir, command, tool_config_copy): command for command in commands}

                    count = 0
                    errors = 0
                    for future in concurrent.futures.as_completed(future_to_command):
                        count = count + 1
                        return_status, return_message = future.result()

                        if return_status:
                            errors = errors + 1
                            move_cursor_down(errors)
                            print(f'{colored(return_message, 'red')}', end='\r', flush=True)
                            move_cursor_up(errors)
                        else:
                            print(f'{return_message}: {count}/{total_contracts}', end='\r', flush=True)
                    move_cursor_down(errors+1)

        print(colored('[+] All insertion tasks completed', 'green'))

if __name__ == "__main__":
    root_dir = sys.argv[1]
    threads = sys.argv[2]
    cpus = sys.argv[3]
    insertion_tools_string = sys.argv[4]
    
    insertion_tools = []
    for tool in insertion_tools_string.split(" "):
        insertion_tools.append(tool)

    execute_processes(root_dir, int(threads), cpus, insertion_tools)  
