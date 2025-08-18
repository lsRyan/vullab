import sys
from openai import OpenAI

if __name__ == "__main__":
    # OpenAI API client
    client = OpenAI()

    # Get list of available models
    available_models = client.models.list()
    
    # Get user provided model
    model = sys.argv[1]

    # Check in OpenAI available models
    for entry in available_models:
        if model == entry.id:
            sys.exit(0) # If found, the model the user provided is ok
    sys.exit(1) # If not match found, alert the user the model selected is not available