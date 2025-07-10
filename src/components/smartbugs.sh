#!bin/bash

ROOT_DIR=$1
ANALYSIS_QNT=$2
THREADS=$3
CPUS=$(( 100000 * $4 ))

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

# Analyze contracts in the execution directory
echo -e "[+] Executing \e[32mSmartBugs\e[0m on baked dataset..."
for dir in $(ls $ROOT_DIR/dataset/baked_dataset); do
	echo -e "[i] Currently working on \e[32m$dir\e[0m"
	bash $ROOT_DIR/smartbugs/smartbugs -t all -f $ROOT_DIR/dataset/baked_dataset/$dir/exec/*.sol --results $ROOT_DIR'/results/${TOOL}/baked_dataset/'$dir'/${FILENAME}' --processes $THREADS --cpu-quota $CPUS --mem-limit 750m --timeout 900 --sarif
done

# Delete execution directory
for dir in $(ls -d $ROOT_DIR/dataset/baked_dataset/*); do
	rm -r "$dir/exec"
done

echo -e "\e[32m[+] All analysis tasks completed\e[0m"
