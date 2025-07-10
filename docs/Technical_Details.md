<div style="text-align: justify"> 

# Technical Details

In this document we present a more in depth explanation of Vullab's implementation by diving into the purpose of each individual code that powers all of the functionalities provided by our tool. With this explanation we hope to offer a better understanding of how implementation works and enable developers to readily understand were ech functionality is located to modify them according to their needs.

## Table of contents
- [Technical Details](#technical-details)
  - [Table of contents](#table-of-contents)
  - [vullab.sh](#vullabsh)
  - [src/modules](#srcmodules)
    - [gpt.sh](#gptsh)
    - [insertion.sh](#insertionsh)
    - [smartbugs.sh](#smartbugssh)
  - [src/utils](#srcutils)
    - [build\_results.py](#build_resultspy)
    - [check\_gpt\_model.py](#check_gpt_modelpy)
    - [csv\_report.py](#csv_reportpy)
    - [exec\_insertion.py](#exec_insertionpy)
    - [gpt\_api.py](#gpt_apipy)
    - [line\_count.sh](#line_countsh)
    - [rectify\_labels.py](#rectify_labelspy)
    - [set\_configs.py](#set_configspy)

## vullab.sh

The `vullab.sh` file is Vullab's main script, as it implements the interface with the user and organizes the control flow that will be undertaken to execute the command. In order achieve that, it includes a parsing function which reads each of the arguments included in the command line with their respective values, if any, and assign them to control variables. These variables determine which module will be executed and with which arguments. All those variables, be control or value ones, have they default values defined at the start of the script.

Importantly, this is the only script which directly access the system `$PWD` variable, which is used as an argument for the modules calls. Despite accessible to all bash scripts throughout the implementation, it was decided to read Vullab's root directory once and resolve the current script directory by  using the provided variable instead of directly using the current directory every time.

## src/modules

The `modules`' scripts implement the execution flow and file management required to execute the tasks specified by the user. Each of the files needed for a specific process will be collected and the corresponding implementations, implemented in `src/utils`, will be called with the appropriate arguments. After the execution of a certain functionality, the outputs are also thoroughly organize, which ensures that the end results directories offer satisfactory readability for the human user and follow the selected standard (e.g. SCWE vulnerability pattern). All scripts in this directory receive the root path of the installation as an argument. This was omitted from each scripts' explanation of for clarity.

### gpt.sh

Orchestrates the gpt execution flow. It first checks if the user have an OpenAI Key already configured in his or hers environment and ensures the selected gpt model, via the `check_gpt_model.py`, is valid. Then, the number of files which the users requested are collected for analysis in a temporary directory and then calls `gpt_api.py`.

### insertion.sh

Orchestrates the insertion tools execution flow. First, it set up HuangGai's configurations by calling `set_configs.py` and then collects all smart contracts in the `dataset/raw_dataset` directory in a temporary folder. After that, the multi-thread insertion tools execution, which is implemented in `exec_insertion.py`, is called with the corresponding arguments, namely the number of threads, number of cpus per thread and the list of selected injection applications selected. Lastly, the temporary directory is deleted and the injected contracts are organized into a more readable names and directory distribution.

### smartbugs.sh

Orchestrates the SmartBugs execution flow. It first collects the number of files which the users requested for analysis in a temporary directory then calls SmartBugs main bash file `smartbugs/smartbugs` with the configured arguments, namely the number of threads and cpus per thread for each of the directories.

## src/utils

The `utils` scripts implement the utilities that power Vullab's main functionalities, be it a core function or a support process. They do not handle execution flows, only singular tasks, such as one or several tool calls. In order to correctly execute their specific tasks, most of the scripts need to know Vullab's working directory. Hence, almost all of them receive the root path of the installation as an argument. This was omitted from each scripts' explanation of for clarity.

### build_results.py

Compares the detection reports compiled in the `summary.csv` file with the inserted dataset's labels to measure the true positive rate of each analysis tool. The script uses the `match-window` flag, optionally configured by the user, to determine a match or a miss. This variable determines how many lines more or less from the label will be considered as a correct detection, despite the vulnerability name. However, some tools do not specify a precise location for an identified bug, but the function. `Maian` and some of the vulnerabilities supported by `slither` are examples of that. In this cases, the script finds the function bounds regarding each label and compare them with the report.

The end results are then compiled in a JSON, `detection_results.json`, file comprised of each vulnerability together with the total entries in the dataset together with the total detections of each tool. This file is then used to plot the true positive rate of each vulnerability. Examples of such graphs can be found in the  readme's "Test Datasets" section.

It is important to note that only the injected vulnerabilities are considered for this end since other bugs present *a priori* in the collected contracts can not be reliably labeled, as per our understanding (more information on this can be found on our research paper).

### check_gpt_model.py

Asserts if a given model is valid or not. The list of available models for the OpenAI API is requested and the script returns **true** or **false**, depending upon the existence of the requested model in the list.

### csv_report.py

Compiles the results from the detection tools in a large table, `summary.csv`, in which the detection tool, the file upon each detection was made, the detection's start and end lines, and the vulnerability name for each entry are highlighted. This is achieved by looping into the detection `.sarif` files in the `results` directory. In the cases in which only the starting line of the vulnerability is provided, the end line is considered as the same line, that is, the vulnerability is considered as being one line long. If a specific line is not provided, the start and end lins are compiled as 0.

### exec_insertion.py

Orchestrates the bug injection process of every insertion tool included. This script receives a list containing the selected applications and load the information regarding each of them from the standardized JSON in `configs/insertion_tools/<tool_name>/<tool_name.json>`, namely the Docker image name, supported vulnerabilities, required volumes and execution command. According to the loaded injection tools' data all the processes will be assembled as a large list, where each entry includes all parameters required to execute a specific vulnerability insertion using a given tool to a given contract.

All the compiled processes are executed by multi-threading them using python's `concurrent` library, which automatically distributes the tasks into the available cores according to the threads specified by the user. The first process of a given tool, however, has an added step to assert that the image can be found locally and download it if it is not. The output management is handled as each task completes, which enables live updates of the execution status and on-terminal printing of execution errors in each process.

### gpt_api.py

Implements OpenAI's API calls with Vullab's specially crafted system prompt for instructing the LLM to behave as a vulnerability detection tool. It also ensures that the called model's output is valid by checking the generated sarif file schema and the presence of the most important fields are present and correctly filled. If the output is invalid, the call is repeated until a valid response is obtained.

This script also ensures that rate limit exceptions are also handled correctly, particularly if the user decides to use more demanding models, such as o1 or o3, which have rather strict call limits. In those cases the call will be repeated up to 5 times, each with an exponentially larger wait time up to 60 seconds.

### line_count.sh

Counts the lines of each of the contract in `/dataset/baked_dataset/*/smart_contract`, upon which a vulnerability was inserted, after processing each file by removing blank lines, comments and non-functional lines (e.g. lines containing just '}' or '(' ). The results are compiled in a file called line_count.txt in `/dataset/baked_dataset/*`, the vulnerability directory.

### rectify_labels.py

Converts the labels from each of the vulnerability insertion tools to the Smart Contract Weaknesses Enumeration (SCWE) standard based on the mapping JSON file `configs/insertion_tools/*/mapping.json`. It also adds a tag to the insertion directory with the enumeration related to each vulnerability, since each of the insertion directories include contracts inserted with a single vulnerability type, for more readability.

### set_configs.py

Handles `HuangGai`'s unique configuration flow. The tool's setup requires a JSON file specifying which vulnerabilities the user wants to insert together with their quantity and the timeout for each process. Hence, this script updates those files according to the user's configurations. Essentially, for each `userNeeds.json` file in `configs\huaggai\threads\*`the respective process timeout will be set. Not the, due to Vullab's multi-thread strategy, the vulnerability insertion quantity is always 1.

</div>