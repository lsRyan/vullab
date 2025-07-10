#!/bin/bash

ROOT_DIR=$1
ANALYSIS_QNT=$2
MODEL=$3

if [[ ! -n "$OPENAI_API_KEY" ]]; then
 	echo -e "\e[31m[!] No chatGPT API key detected! Make sure you have a key saved as an environment variable! For more information please check the openAI API platform documentation.\e[0m"
	exit 1
fi

python3 $ROOT_DIR/src/utils/check_gpt_model.py $MODEL
exit_status=$?
if [ $exit_status -eq 1 ]; then
 	echo -e "\e[31m[!] The model $MODEL you selected is not available! Please refer to the openAI API documentation for available models.\e[0m"
	exit 1
fi
	
# Filter contracts by line count
echo "[+] Collecting dataset for analysis..."
for dir in $(ls -d $ROOT_DIR/dataset/baked_dataset/*); do
	if [ "$ANALYSIS_QNT" == "all" ];  then
		# Get all contracts
		contracts=$(cat $dir/line_count.txt | awk '{print $1}')
	else
		# Get only the largest $ANALYSIS_QNT contracts
		contracts=$(cat $dir/line_count.txt | head -$ANALYSIS_QNT | awk '{print $1}')
	fi

	# Ensure no directory with the same name exists
	rm -rf $dir/exec

	# Create an execution directory
	mkdir -p $dir/exec

	# Copy selected files to the execution directory
	for contract in "${contracts[@]}"; do
		cp $contract $dir/exec
	done
done

# Executing GPT in baked dataset
echo -e "[+] Executing \e[32m$MODEL\e[0m on baked dataset..."
for dir in $(ls $ROOT_DIR/dataset/baked_dataset); do
	echo -e "[i] Currently working on \e[32m$dir\e[0m"
	for contract in $(ls $ROOT_DIR/dataset/baked_dataset/$dir/exec); do
		if [ ! -d $ROOT_DIR/results/$MODEL/baked_dataset/$dir/$contract ]; then
			mkdir -p $ROOT_DIR/results/$MODEL/baked_dataset/$dir/$contract
		fi
        code=$(cat $ROOT_DIR/dataset/baked_dataset/$dir/exec/$contract | sed -e 's|//.*|// comment|' -e '/\/\*/,/\*\//{/\/\*/!{/\*\//!s|.*|comment|}}')
		echo "$code" | python3 $ROOT_DIR/src/utils/gpt_api.py $MODEL $ROOT_DIR/results/$MODEL/baked_dataset/$dir/$contract/result.sarif
		wait
	done
done

# Delete execution directory
for dir in $(ls -d $ROOT_DIR/dataset/baked_dataset/*); do
	rm -r "$dir/exec"
done

echo -e "\e[32m[+] All analysis tasks completed\e[0m"
