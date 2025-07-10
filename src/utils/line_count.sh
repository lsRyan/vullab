#!bin/bash

BAKED_DIR=$1

# Create report with the line count for each smart contract
for dir in $(ls -d $BAKED_DIR/*); do
    
    #Array with the path to each contract and the number of lines
    contracts_line_count=()
	for contract in $(ls $dir/smart_contracts); do
		#For each contract, count the number of lines excluding comments and blank lines
        number_of_lines=$(cat $dir/smart_contracts/$contract | sed -e "s/;/\n/g" | sed "s|//.*||; /\/\*/,/\*\//d" | sed -e "s/{/ /g; s/}/ /g; s/\[/ /g; s/\]/ /g" | sed '/^\s*$/d' | wc -l)
		
        #Add to the array
        contracts_line_count+=("$dir/smart_contracts/$contract $number_of_lines")
	done

    #Organize in descending order in the output file
    printf "%s\n" "${contracts_line_count[@]}" | sort -k2 -nr > $dir/line_count.txt
done