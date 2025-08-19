# Usage Manual

VulLab was implemented with a command line interface to be used in any Linux terminal. It functions by linearly parsing the specified flags with, if needed, their respective configuration values.

## Command line interface
```
vullab.sh [--threads THREADS] [--cpus CPUS]
          [--solidifi] [--huanggai TIMEOUT]
          [--analyze QUANTITY] [--gpt QUANTITY MODEL] 
          [--match-window MATCH_WINDOW] [--build] 
          [--help]
```

## Options
`--threads THREADS`, `-t THREADS` Configures how many threads will run simultaneously during insertion and detection phases of the execution. Set as 1 by default, which means sequential execution.

`--cpus CPUS`, `-c CPUS` Configures how many CPUs will be assigned to each process. As each thread runs as a container, this setting means how many cpu power each container will receive. Set as 1 by default.

`--solidifi`, `-s` Executes SolidiFi in all of the `.sol` files located in `\dataset\raw_dataset`. The tool will insert as many vulnerabilities as it can in all of the contracts it finds suitable. The inserted contracts will be located at `\dataset\baked_dataset\*\smart_contracts` and the labels will be located in `\dataset\baked_dataset\*\labels`, where `*` represents a directory with the name of each supported vulnerability.

`--huanggai TIMEOUT`, `-u TIMEOUT` Executes HuangGai in all of the `.sol` files located in `\dataset\raw_dataset`. The inserted contracts will be located at `\dataset\baked_dataset\*\smart_contracts` and the labels will be located in `\dataset\baked_dataset\*\labels`, where `*` represents a directory with the name of each supported vulnerability. The optional configuration TIMEOUT corresponds to the timeout of each HuangGai container, which is set as 0.5 minutes by default.

`--analyze QUANTITY`, `-a QUANTITY` Executes `SmartBugs` in all of the contracts located in `\dataset\baked_dataset\*\smart_contracts`. Note that, despite supporting several other detection tools, only [confuzzius](https://github.com/christoftorres/ConFuzzius), [conkas](https://github.com/smartbugs/conkas), [honeybadger](https://github.com/christoftorres/HoneyBadger), [maian](https://github.com/smartbugs/MAIAN), [manticore](https://github.com/trailofbits/manticore), [mythril](https://github.com/ConsenSys/mythril), [osiris](https://github.com/christoftorres/Osiris), [oyente](https://github.com/smartbugs/oyente), [securify](https://github.com/eth-sri/securify), [semgrep](https://github.com/Decurity/semgrep-smart-contracts), [sfuzz](https://github.com/duytai/sFuzz), [slither](https://github.com/crytic/slither), [smartcheck](https://github.com/smartdec/smartcheck) and [solhint](https://github.com/protofire/solhint), will be used. These tools are the ones that support Solidity source code. When the QUANTITY configuration number is set, it selectively executes the analysis tools on the specified number of the most complex smart contracts per vulnerability within the database. The complexity of each smart contract was determined by a straightforward metric: the count of functional lines of code, which is set as `all` by default.

`--gpt QUANTITY MODEL`, `-g QUANTITY MODEL` **Note that GPT's API is paid!** Executes `GPT` with a pre-determined system prompt directing the model to behave as a state-of-the-art smart contract vulnerability detection tool. The target are all `.sol` files located in `\dataset\raw_dataset`. The results obtained will be compiled in the `results/MODEL` repository. When the QUANTITY configuration number is set, it selectively executes the analysis tools on the specified number of the most complex smart contracts per vulnerability within the database. Set as "all" by default. The MODEL configuration enables the selection of any of the available models. Set as gpt-4o-mini as default. If this option is present the results will automatically be compiled in the file `results\summary.csv` and will be graphically presented in `results\baked_dataset_results.png`.

`--match-window`, `-m` The match window is defined as how many lines more then the label definition is considered a 'hit' when comparing the detection results with the respective labels. For example, if a certain vulnerability is labeled as starting at line 10 and ending at line 20, a match window of 5 would mean that any detection of the correct vulnerability in the range of lines 5 through 25 will be considered a hit.

`--build`, `-b` Executes the building scripts, (re-)generating the CSV detection report and the accuracy statistics graph according to the labels.

`--help`, `-h` Will show the help menu. It contains a summary of the usage information.