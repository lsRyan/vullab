import sys
from openai import OpenAI

if __name__ == "__main__":
    client = OpenAI()
    available_models = client.models.list()
    model = sys.argv[1]

    for entry in available_models:
        if model == entry.id:
            sys.exit(0)
    sys.exit(1)