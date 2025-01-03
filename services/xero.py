import requests
from xero_python.exceptions.http_status_exceptions import AccountingBadRequestException
from config import config
from services.auth import load_credentials, generate_token

def accounting_create_receipt(receipts: dict):
    token = config.XERO_ACCESS_TOKEN
    url = f"{config.XERO_V2_BASE_URL}/Receipts"

    token = load_credentials()

    try:
        headers = {
            "Authorization": f"Bearer {token.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Xero-Tenant-Id": config.XERO_TENANT_ID
        }

        response = requests.post(url, json=receipts, headers=headers)
        if response.status_code == 200:
            return response.json()

        elif response.status_code >= 400 and response.status_code < 500:
            new_token = generate_token(token.refresh_token)
            headers["Authorization"] = f"Bearer {new_token.access_token}"
            
            response = requests.post(url, json=receipts, headers=headers)
            return response.json()
        else:
            print(response.json())
    
    except AccountingBadRequestException as e:
        print("Exception when calling AccountingApi->createReceipt: %s\n" % e)