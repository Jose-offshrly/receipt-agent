import json

def load_accounts():
    # Read and load the JSON file into a dictionary
    input_file = "data/accounts.json"
    with open(input_file, "r") as file:
        accounts = json.load(file)
        return accounts
