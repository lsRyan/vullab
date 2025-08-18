#!bin/bash

# Input variables
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
    # Set Huanggai config files according to user configurations
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
	# Get all files in raw_dataset and copy them to .temp
	for file in ${contracts[@]}; do
		# Getting files
		file_name=$(basename $file)
		file_name=${file_name%.*}

		# Creating .temp dir and copying contracts 
		mkdir -p $ROOT_DIR/dataset/raw_dataset/.temp/$file_name
		cp $file $ROOT_DIR/dataset/raw_dataset/.temp/$file_name
	done

	echo "[i] ${#contracts[@]} contracts collected"
}

# Organize Huanggai outputs from vanilla directories to structured directories
organize_huanggai_outputs() {
	# Delete Huanggai's secondary files (not needed)
	rm $ROOT_DIR/dataset/baked_dataset/securityAbandonerAndInjector/*.py
	
	# For each vanilla directory
	for dir in $ROOT_DIR/dataset/baked_dataset/securityAbandonerAndInjector/*; do
		# Get vulnerability name
		dir_name=$(basename $dir)
		
		# For each vulnerability insertion directory
		if find $ROOT_DIR/dataset/baked_dataset/securityAbandonerAndInjector/$dir_name/dataset -mindepth 1 -maxdepth 1 | read; then
			# Create structured directories
			mkdir $ROOT_DIR/dataset/baked_dataset/$dir_name
			mkdir $ROOT_DIR/dataset/baked_dataset/$dir_name/smart_contracts
			mkdir $ROOT_DIR/dataset/baked_dataset/$dir_name/labels
	
			# Move contracts to their respective directories in the new structure
			for file in $ROOT_DIR/dataset/baked_dataset/securityAbandonerAndInjector/$dir_name/dataset/*.sol; do
				mv $file $ROOT_DIR/dataset/baked_dataset/$dir_name/smart_contracts
			done

			# Move labels to their respective directories in the new structure
			for file in $ROOT_DIR/dataset/baked_dataset/securityAbandonerAndInjector/$dir_name/dataset/*.txt; do
				mv $file $ROOT_DIR/dataset/baked_dataset/$dir_name/labels
			done
		fi
    done

	# Delete Huanggai's vanilla directory
    rm -r $ROOT_DIR/dataset/baked_dataset/securityAbandonerAndInjector
}

# Organize Solidifi outputs from vanilla directories to structured directories
organize_solidifi_outputs() {
	# For each vanilla directory
	for dir in $ROOT_DIR/dataset/baked_dataset/buggy/*; do
		# Get vulnerability name
		dir_name=$(basename $dir)

		# Create structured directories
		mkdir $ROOT_DIR/dataset/baked_dataset/$dir_name
		mkdir $ROOT_DIR/dataset/baked_dataset/$dir_name/smart_contracts
		mkdir $ROOT_DIR/dataset/baked_dataset/$dir_name/labels
			
		# Move contracts to their respective directories in the new structure
		for file in $ROOT_DIR/dataset/baked_dataset/buggy/$dir_name/*.sol; do
			mv $file $ROOT_DIR/dataset/baked_dataset/$dir_name/smart_contracts
		done

		# Move labels to their respective directories in the new structure
		for file in $ROOT_DIR/dataset/baked_dataset/buggy/$dir_name/*.csv; do
			mv $file $ROOT_DIR/dataset/baked_dataset/$dir_name/labels
		done	

	done

	# Delete Solidifi's vanilla directory
	rm -r $ROOT_DIR/dataset/baked_dataset/buggy
}

# Set Huanggai configuration files
set_configuration

# Create temporary execution folder
execution_setup

# Execute insertion script
python3 $ROOT_DIR/src/utils/exec_insertion.py $PWD $THREADS $CPUS "${TOOLS[*]}"

# Delete temp directory
rm -r $ROOT_DIR/dataset/raw_dataset/.temp

# Organize output directories
echo -e "[+] Building output directories..."
for tool in "${TOOLS[@]}"; do
	if [ "$tool" = "huanggai" ]; then # If the user selected Huanggai
		# Organize Huangai output directories
		organize_huanggai_outputs
	elif [ "$tool" = "solidifi" ]; then #If the user selected Solidifi
		# Organize Huangai output directories
		organize_solidifi_outputs
	fi
done

# Rectify labels from Huanggai and SOlidifi standard to SCWE + SCWEX
python3 $ROOT_DIR/src/utils/rectify_labels.py $ROOT_DIR

# Get functional lines from each inserted contracts
bash $ROOT_DIR/src/utils/line_count.sh $ROOT_DIR/dataset/baked_dataset

echo -e "[+] Directories build"