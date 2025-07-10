import sys, json, jsonschema, requests
from openai import OpenAI
from termcolor import colored
from tenacity import retry, stop_after_attempt, wait_random_exponential

# This function, in case of failure,  will be executed up to 5 times, each with a random exponential delay according to the configuration
# This is to handle cases in with the selected model is rate limited, particularly more expensive models
@retry(wait=wait_random_exponential(min=10, max=60), stop=stop_after_attempt(5))
def analyze_with_gpt(client, model, prompt):
    # Definition of the system prompt
    system_prompt = '''
    You are a state-of-the-art vulnerability detection tool for Ethereum smart contracts.
    Your task is to analyze the solidity code that will be sent to you and respond in the sarif version 2.1.0 format, using the following template:
    
    {
      "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
      "runs": [
          {
              "results": [],
              "tool": {
                  "driver": {
                      "informationUri": "https://platform.openai.com/docs/guides/chat",
                      "name": "GPT",
                      "rules": [],
                      "version": "gpt"
                  }
              }
          }
      ],
      "version": "2.1.0"
    }

    Each of the vulnerabilities you found should be added to the "results" list, and should follow the template below. 
    You should add all vulnerabilities you found, even when you detect a same vulnerability type in several different parts of the contract.
    Everything that is between tags << and >> represents a value that you should fill according to the vulnerabilities you detected:

    {
        "locations": [
            {
                "message": {
                    "text": "<<Vulnerability name>>"
                },
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": "<<name of the Solidity contract>>"
                    },
                    "region": {
                        "endLine": <<vulnerability last line>>,
                        "startLine": <<vulnerability first line>>
                    }
                }
            }
        ],
        "message": {
            "text": "<<Vulnerability description>>"
        },
        "ruleId": "<<SCWE code>>"
    }
    
    In the "rules" list you should list every unique vulnerability rule you found analyzing the contract. That is, every unique vulnerability ruleId you found should be represented only once in this list, regardless of how many of the same kind of vulnerability you found.
    For each of such entries you should follow the following template, in which everything that is between tags << and >> represents a value that you should fill according to the vulnerabilities you detected:

    {
        "id": "<<SCWE code>>",
        "name": "(<<SCWE code>>) <<name of the vulnerability corresponding to the SCWE code>>"
    },

    Each vulnerability you found should be classified according to the following vulnerability list:

    (SCWE-001) Improper Contract Architecture
    (SCWE-002) Excessive Contract Complexity
    (SCWE-003) Lack of Modularity
    (SCWE-004) Uncaught Exceptions
    (SCWE-005) Insecure Upgradeable Proxy Design
    (SCWE-006) Inconsistent Inheritance Hierarchy
    (SCWE-007) Presence of Unused Variables
    (SCWE-008) Hardcoded Constants
    (SCWE-009) Deprecated Variable and Function Usage
    (SCWE-010) Shadowing Variables and Functions
    (SCWE-011) Insecure ABI Encoding and Decoding
    (SCWE-012) Lack of Multisig Governance
    (SCWE-013) Unauthorized Parameter Changes
    (SCWE-014) Lack of Emergency Stop Mechanism
    (SCWE-015) Poor Governance Documentation
    (SCWE-016) Insufficient Authorization Checks
    (SCWE-017) Privileged Role Mismanagement
    (SCWE-018) Use of tx.origin for Authorization
    (SCWE-019) Insecure Signature Verification
    (SCWE-020) Absence of Time-Locked Functions
    (SCWE-021) Unsecured Data Transmission
    (SCWE-022) Message Replay Vulnerabilities
    (SCWE-023) Lack of Communication Authenticity
    (SCWE-024) Weak Randomness Sources
    (SCWE-025) Improper Cryptographic Key Management
    (SCWE-026) Insufficient Hash Verification
    (SCWE-027) Vulnerable Cryptographic Algorithms
    (SCWE-028) Price Oracle Manipulation
    (SCWE-029) Lack of Decentralized Oracle Sources
    (SCWE-030) Insecure Oracle Data Updates
    (SCWE-031) Insecure use of Block Variables
    (SCWE-032) Dependency on Block Gas Limit
    (SCWE-033) Chain Split Risks
    (SCWE-034) Insecure Cross-Chain Messaging
    (SCWE-035) Insecure Delegatecall Usage
    (SCWE-036) Inadequate Gas Limit Handling
    (SCWE-037) Insufficient Protection Against Front-Running
    (SCWE-038) Insecure Use of Selfdestruct
    (SCWE-039) Insecure Use of Inline Assembly
    (SCWE-040) Incorrect Storage Packing
    (SCWE-041) Unsafe Downcasting
    (SCWE-042) Insecure Use of External Calls
    (SCWE-043) Insecure Use of Fallback Functions
    (SCWE-044) Insecure Use of Storage
    (SCWE-045) Insecure Use of Modifiers
    (SCWE-046) Reentrancy Attacks
    (SCWE-047) Integer Overflows and Underflows
    (SCWE-048) Unchecked Call Return Value
    (SCWE-049) Unprotected Ether Withdrawal
    (SCWE-050) Unprotected SELFDESTRUCT Instruction
    (SCWE-051) Improper Use of CREATE2 for Contract Deployment
    (SCWE-052) Transaction Order Dependence
    (SCWE-053) Improper Deletion of Mappings
    (SCWE-054) Signature Malleability SCSVS-CRYPTO
    (SCWE-055) Missing Protection against Signature Replay Attacks
    (SCWE-056) Lack of Proper Signature Verification
    (SCWE-057) Write to Arbitrary Storage Location
    (SCWE-058) DoS with Block Gas Limit
    (SCWE-059) Insufficient Gas Griefing
    (SCWE-060) Floating Pragma
    (SCWE-061) Outdated Compiler Version
    (SCWE-062) Dead Code
    (SCWE-063) Insecure Event Emission
    (SCWE-064) Incorrect Inheritance Order
    (SCWE-065) Block Values as a Proxy for Time
    (SCWE-066) Incorrect Handling of Bitwise Operations
    (SCWE-067) Assert Violation
    (SCWE-068) State Variable Default Visibility
    (SCWE-069) Shadowing State Variables
    (SCWE-070) Incorrect Constructor Name
    (SCWE-071) Uninitialized Storage Pointer
    (SCWE-072) Use of Deprecated Solidity Functions
    (SCWE-073) Message Call with Hardcoded Gas Amount
    (SCWE-074) Hash Collisions with Multiple Variable Length Arguments
    (SCWE-075) Incorrect Ether Balance Tracking
    (SCWE-076) Right-To-Left-Override Control Character (U+202E)
    (SCWE-077) Lack of Rate Limiting
    (SCWE-078) Improper Handling of Ether Transfers
    (SCWE-079) Insecure Use of Transfer and Send
    (SCWE-080) Incorrect Type Conversion
    (SCWE-081) Improper Handling of Nonce
    (SCWE-082) Lack of Proper Gas Management
    (SCWE-083) Failure to Handle Edge Cases
    (SCWE-084) Insecure Use of blockhash
    (SCWEX-001) Absence of Ether Transfer Functions
    (SCWEX-002) Lack of Address Input Validation
    (SCWEX-003) Inadequate Function Visibility
    (SCWEX-004) Inadequate Naming Convention
    (SCWEX-005) Use of address(this).balance in Comparison Statements
    (SCWEX-006) Public Access to non-Public Variables
    
    Despite the sarif response, you should not return anything else.
    '''

    # Call to the GPT API
    response = client.chat.completions.create(
      model=model,     
      messages=[
          {"role": "system", "content": system_prompt},
          {"role": "user", "content": prompt},
      ]
    )

    # Extract the reply from the response
    return response

def get_sarif_schema():
    return(requests.get("https://json.schemastore.org/sarif-2.1.0").json())

def assert_sarif_format(sarif_report, sarif_schema):
    try:
        # Validate if sarif can be opened
        sarif_data = json.loads(sarif_report)

        # Validate sarif schema
        jsonschema.validate(instance=sarif_data, schema=sarif_schema)

        # Validate rule ids match
        sarif_entries = sarif_data["runs"][0]["results"] # Vulnerabilities detected
        rule_ids = [id["id"] for id in sarif_data["runs"][0]["tool"]["driver"]["rules"]] # IDs from the detected vulnerabilities
        
        # For each of the detected vulnerabilities...
        for entry in sarif_entries:
            # Its id should be present in the 'rules' list, under 'tool' and 'driver' in the sarif
            if entry["ruleId"] not in rule_ids:
                raise Exception(colored("The 'rules' list, under 'tool' and 'driver' was not set correctly", "red"))
        
        # If everything is ok
        return True

    except:
        # If any of the tests failed
        return False

if __name__ == "__main__":
    client = OpenAI()
    model = sys.argv[1]
    sarif_dir = sys.argv[2]
    smart_contract_src = sys.stdin.read()
    
    # Get the sarif JSON schema
    sarif_schema = get_sarif_schema()
    # Analyse the contract until a valid response is obtained
    while True:
        # Get response from the GPT
        response = analyze_with_gpt(client, model, smart_contract_src)
        report = response.choices[0].message.content
        
        # Assert that the result is in the correct format
        if assert_sarif_format(report, sarif_schema):
            break

    # Write the report into a .sarif file
    with open(sarif_dir, "w") as sarif_file:
        sarif_file.write(report)
