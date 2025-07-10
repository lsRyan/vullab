#!bin/bash

ROOT_DIR=$1
TOOLS=($2)
THREADS=$3
CPUS=$4
HUANGGAI_TIMEOUT=$5

# Directory containing the files to be processed
FILES_DIR=$ROOT_DIR/dataset/raw_dataset
mapfile -t FILES < <(find $FILES_DIR/ -maxdepth 1 -mindepth 1 -type f| sort)

# Configure HuangGai
set_configuration() {
    # Set Huanggai Config Files
	python3 $ROOT_DIR/src/utils/set_configs.py $ROOT_DIR $HUANGGAI_TIMEOUT
}

# Initialize directories
execution_setup() {
	contracts_dir=$ROOT_DIR/dataset/raw_dataset
	mapfile -t contracts < <(find $contracts_dir/ -maxdepth 1 -mindepth 1 -type f| sort)
	
	# Ensure no directory with the same name exists
	rm -rf $ROOT_DIR/dataset/raw_dataset/.temp
	
	# Creating temp directory
	mkdir -p $ROOT_DIR/dataset/raw_dataset/.temp

	echo "[+] Collecting dataset for insertion..."
	for file in ${contracts[@]}; do
		file_name=$(basename $file)
		file_name=${file_name%.*}
	
		mkdir -p $ROOT_DIR/dataset/raw_dataset/.temp/$file_name
		cp $file $ROOT_DIR/dataset/raw_dataset/.temp/$file_name
	done

	echo "[i] ${#contracts[@]} contracts collected"
}

# Organize outputs
organize_huanggai_outputs() {
	rm $ROOT_DIR/dataset/baked_dataset/securityAbandonerAndInjector/*.py
	for dir in $ROOT_DIR/dataset/baked_dataset/securityAbandonerAndInjector/*; do
		dir_name=$(basename $dir)
		if find $ROOT_DIR/dataset/baked_dataset/securityAbandonerAndInjector/$dir_name/dataset -mindepth 1 -maxdepth 1 | read; then
			mkdir $ROOT_DIR/dataset/baked_dataset/$dir_name
			mkdir $ROOT_DIR/dataset/baked_dataset/$dir_name/smart_contracts
			mkdir $ROOT_DIR/dataset/baked_dataset/$dir_name/labels
	
			for file in $ROOT_DIR/dataset/baked_dataset/securityAbandonerAndInjector/$dir_name/dataset/*.sol; do
				mv $file $ROOT_DIR/dataset/baked_dataset/$dir_name/smart_contracts
			done
			for file in $ROOT_DIR/dataset/baked_dataset/securityAbandonerAndInjector/$dir_name/dataset/*.txt; do
				mv $file $ROOT_DIR/dataset/baked_dataset/$dir_name/labels
			done
		fi
    done
    rm -r $ROOT_DIR/dataset/baked_dataset/securityAbandonerAndInjector
}

organize_solidifi_outputs() {
	for dir in $ROOT_DIR/dataset/baked_dataset/buggy/*; do
		dir_name=$(basename $dir)
		mkdir $ROOT_DIR/dataset/baked_dataset/$dir_name
		mkdir $ROOT_DIR/dataset/baked_dataset/$dir_name/smart_contracts
		mkdir $ROOT_DIR/dataset/baked_dataset/$dir_name/labels
			
		for file in $ROOT_DIR/dataset/baked_dataset/buggy/$dir_name/*.sol; do
			mv $file $ROOT_DIR/dataset/baked_dataset/$dir_name/smart_contracts
		done
		for file in $ROOT_DIR/dataset/baked_dataset/buggy/$dir_name/*.csv; do
			mv $file $ROOT_DIR/dataset/baked_dataset/$dir_name/labels
		done	

	done
	rm -r $ROOT_DIR/dataset/baked_dataset/buggy
}


set_configuration
execution_setup
python3 $ROOT_DIR/src/utils/exec_insertion.py $PWD $THREADS $CPUS "${TOOLS[*]}"

# Delete temp directory
rm -r $ROOT_DIR/dataset/raw_dataset/.temp

# Organize output directories
echo -e "[+] Building output directories..."
for tool in "${TOOLS[@]}"; do
	if [ "$tool" = "huanggai" ]; then
		organize_huanggai_outputs
	elif [ "$tool" = "solidifi" ]; then
		organize_solidifi_outputs
	fi
done
python3 $ROOT_DIR/src/utils/rectify_labels.py $ROOT_DIR
bash $ROOT_DIR/src/utils/line_count.sh $ROOT_DIR/dataset/baked_dataset
echo -e "[+] Directories build"