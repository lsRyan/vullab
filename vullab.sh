#!bin/bash

### Execution Variables ###
# Parallel configuration
threads=1

# Cores per Docker container 
cpus=1

# Insertion tools
tools=()
huangGai_timeout=0.5

# Count lines of inserted contracts
count_lines=false

# Label rectification
rectify_labels=false

# Analysis configuration
#Smartbugs
analyze=false
smartbugs_analysis_qnt=all
#GPT
gpt=false
gpt_analysis_qnt=all
gpt_model=gpt-4o-mini
#Number of line more or less from labels 
#to be considered a successful detection
match_window="5"

# (Re-)Building Results configuration
build_results=false

# Help
help=false

### Parse flags ###
while [[ $# -gt 0 ]]; do
	case "$1" in
		-h|--help)
		help=true
		break
		;;

		-c|--cpus)
		shift
		threads=$1
		;;
		
		-t|--threads)
		shift
		threads=$1
		;;

		-u|--huanggai)
		tools+=("huanggai")

		re='^[0-9]+(\.[0-9]+)?$'
		if [[ $2 =~ $re ]] ; then
   			shift
   			huangGai_timeout=$1
		fi
		;;
		
		-s|--solidifi)
		tools+=("solidifi")
		;;
		
		-a|--analyze)
		analyze=true

		re='^[0-9]+$'
		if [[ $2 =~ $re ]] ; then
   			shift
   			smartbugs_analysis_qnt=$1
		fi
		;;

		-g|--gpt)
		gpt=true

		re='^[0-9]+$'
		if [[ $2 =~ $re ]] ; then
   			shift
   			gpt_analysis_qnt=$1
		fi

		re='^[^-]'
		if [[ $2 =~ $re ]] ; then
   			shift
   			gpt_model=$1
		fi
		;;
		
		-b|--build)
		build_results=true
		;;
		
		-m|--match-window)
		shift
		match_window=$1
		;;

		*)
		echo "Unknown option: $1"
		exit 1
		;;
		
	esac
	shift
done

echo -e "\e[32m
    Thank you for using VulLab, the smart contract vulnerability laboratory!

	    º
	     o    
	   (  )
	   | º|             _   __       _ 
	   |o |/\   /\_   _| | / /  __ _| |__
	  /~~~~\ \ / / | | | |/ /  / _' | '_ \ 
	 /      \ V /| |_| | / /__| (_| | |_) |
	/________\_/  \__,_|_\____/\__,_|_.__/ 
\e[0m"

if [ "$help" = "true" ]; then
	echo "
	Usage: $(basename "$0") [--parallel NUMBER_OF_CORES] [--solidifi]
                            [--huanggai NUMBER_OF_CONTRACTS INSERTION_TIMEOUT]
                            [--analyze NUMBER_OF_CONTRACTS] [--gpt NUMBER_OF_CONTRACTS]
							[--help]
	
	Description:
		VulLab is a framework which encapsulates three state of the art tools for smart contract's security analysis:
		- SolidiFI 
		- HuangGai
		- SmartBugs 2.0
		The first two are bug injectors and the third is a framework that brings together several vulnerability detection tools.
		Besides, it offers a manually crafted dataset of vulnerable smart contracts together with their respective labels.
		VulLab's use case is the validation and comparison with other state of the art tools of vulnerability detection applications under development.

	Options:
	  -h, --help             Show this help message and exit.
	  
	  -t, --threads N        Configures how many threads will run simultaneously during insertion and detection phases of the execution. (default: 1).
	  
	  -c, --cpus			 Configures how many CPUs will be assigned to each process during insertion and detection phases of the execution. (default: 1).
	  
	  -s, --solidifi         Executes SolidiFI bug injection tool in the .sol files in $(basename "$PWD")/dataset/raw_dataset.
	  
	  -u, --huanggai N       Executes HuangGai bug injection tool in the .sol files in $(basename "$PWD")/dataset/raw_dataset. 
	                         Takes as optional argument the timeout for the execution of each HuangGai container in minutes. 
							 Note than this argument can be a float, such as 0.2. (default: 0.5). 
	  
	  -a, --analyze N        Executes SmartBugs 2.0 in the selected number of .sol files in $(basename "$PWD")/dataset/manual_dataset.
	  						 Takes as optional argument the quantity of contracts for vulnerability in which SmartBugs 2.0 will be executed for each vulnerability. (default: all).
							 The contracts are sorted by line count considering only functional lines.
	  
	  -g, --gpt N S          Executes GPT as a state-of-the-art vulnerability detection tool in the selected number of .sol files in $(basename "$PWD")/dataset/manual_dataset via OpenAI's API.
	                         Takes as optional argument the quantity of contracts for vulnerability  in which GPT will be executed for each vulnerability. (default: all).
							 The contracts are sorted by line count considering only functional lines.
							 Takes as optional argument the model from GPT API will be used. (default: gpt-4o-mini).

	  -m, --match-window N   Configure the match window when comparing the detection results with the labels. (default: 5).

	  -b, --build            Executes the building scripts, (re-)generating the CSV detection report and the accuracy statistics graph according to the labels.

	Examples:
	  $(basename "$0") -s --analyze                     Executes SolidiFI. Also executes Smartbugs 2.0 in all inserted contracts.
	  $(basename "$0") -t 4 -c 2 -u 2.0 -g              Executes four instances of HuangGai with 2 cpus each and a 2 minutes timeout. Also executes gpt in all inserted contracts. 
	  $(basename "$0") --solidifi --g 10 gpt-4.1-nano   Executes SolidiFI. Also executes gpt model 4.1-nano in the 10 largest contracts for each inserted vulnerability.
	
	Notes:
	  - For the options 'N' means 'number' and 'S' means string (without quotes).
	  - We recommend using the flags in the following order -t, -c, -u, -s, -a, -g, -m, -b. 
	    You can also use them separately, calling $(basename "$0") several times.
	  - Use long options (e.g., --help) or short options (e.g., -h) as needed.
	"
	exit 0
fi

if (( ${#tools[@]} )); then
	bash $PWD/src/components/insertion.sh $PWD "${tools[*]}" $threads $cpus $huangGai_timeout
fi

if [ "$analyze" = "true" ]; then
	bash $PWD/src/components/smartbugs.sh $PWD $smartbugs_analysis_qnt $threads $cpus
	build_results=true
fi

if [ "$gpt" = "true" ]; then
	bash $PWD/src/components/gpt.sh $PWD $gpt_analysis_qnt $gpt_model
	build_results=true
fi

if [ "$build_results" = "true" ]; then
	python3 $PWD/src/utils/csv_report.py $PWD
	python3 $PWD/src/utils/build_results.py $PWD $match_window
fi
