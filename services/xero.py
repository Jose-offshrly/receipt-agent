import requests
from xero_python.exceptions.http_status_exceptions import AccountingBadRequestException
from config import config
from services.auth import load_credentials, generate_token
from urllib.parse import urlencode


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
            response = response.json()
            print("Xero api respond: ", response)
            return response

        elif response.status_code >= 400 and response.status_code < 500:
            new_token = generate_token(token.refresh_token)
            headers["Authorization"] = f"Bearer {new_token.access_token}"
            
            response = requests.post(url, json=receipts, headers=headers)
            return response.json()
        else:
            print(response.json())
    
    except AccountingBadRequestException as e:
        print("Exception when calling AccountingApi->createReceipt: %s\n" % e)



def get_tax(name: str):
    token = config.XERO_ACCESS_TOKEN
    params = urlencode({"where": f'name=="{name}"'})
    url = f"{config.XERO_V2_BASE_URL}/TaxRates?{params}"

    token = load_credentials()

    try:
        headers = {
            "Authorization": f"Bearer {token.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Xero-Tenant-Id": config.XERO_TENANT_ID
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            response = response.json()
            # print("Xero api respond: ", response)
            return response

        elif response.status_code >= 400 and response.status_code < 500:
            new_token = generate_token(token.refresh_token)
            headers["Authorization"] = f"Bearer {new_token.access_token}"
            
            response = requests.get(url, headers=headers)
            return response.json()
        else:
            print(response.json())
    
    except AccountingBadRequestException as e:
        print("Exception when calling AccountingApi->createReceipt: %s\n" % e)

def create_tax(name: str, rate: float):
    token = config.XERO_ACCESS_TOKEN
    url = f"{config.XERO_V2_BASE_URL}/TaxRates"
    
    token = load_credentials()

    try:
        headers = {
            "Authorization": f"Bearer {token.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Xero-Tenant-Id": config.XERO_TENANT_ID
        }
        body = {
            "TaxRates": [
                {
                "Name": name,
                "TaxComponents": [
                    {
                    "Name": name,
                    "Rate": float(rate)
                    }
                ]
                }
            ]
        }

        response = requests.post(url, json=body, headers=headers)
        if response.status_code == 200:
            response = response.json()
            print("Xero api respond: ", response)
            return response

        elif response.status_code >= 400 and response.status_code < 500:
            new_token = generate_token(token.refresh_token)
            headers["Authorization"] = f"Bearer {new_token.access_token}"
            
            response = requests.get(url, json=body, headers=headers)
            return response.json()
        else:
            print("failed")
            print(response.json())
    
    except AccountingBadRequestException as e:
        print("Exception when calling AccountingApi->createReceipt: %s\n" % e)


def get_or_create_tax_rate(name, rate):

    tax = get_tax(name)
    if len(tax["TaxRates"]) > 0:
        return tax
    else:
        print("Tax Rate does not exist, creating...")
        tax = create_tax(name, rate)
        return tax