import requests, json, os
from requests.auth import HTTPBasicAuth
from xero_python.exceptions.http_status_exceptions import AccountingBadRequestException
from config import config
from models.auth import Auth

def generate_token(refresh_token: str) -> Auth:
    print("requesting new access_token")

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    response = requests.post(
        config.XERO_TOKEN_URL, 
        data=data, 
        auth=HTTPBasicAuth(
            config.XERO_CLIENT_ID, 
            config.XERO_CLIENT_SECRET
        )
    )

    if response.status_code == 200:
        token_data = response.json()
        auth = Auth(**token_data)

        os.makedirs("credentials", exist_ok=True)
        with open("credentials/auth.json", "w") as f:
            json.dump(auth.model_dump(), f, indent=4)

        return auth
    else:
        print("Error:", response.json())
        response.raise_for_status()


def load_credentials() -> Auth:
    
    with open("credentials/auth.json", "r") as f:
        data = json.load(f)
        return Auth(**data)