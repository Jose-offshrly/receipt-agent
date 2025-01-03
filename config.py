import os
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
load_dotenv(override=True)

class User(BaseModel):
    user_id: str
    contact_id: str


class Settings(BaseSettings):
    XERO_CLIENT_ID: str = os.getenv("XERO_CLIENT_ID")
    XERO_CLIENT_SECRET: str = os.getenv("XERO_CLIENT_SECRET")
    XERO_ACCESS_TOKEN: str = os.getenv("XERO_ACCESS_TOKEN")
    XERO_REFRESH_TOKEN: str = os.getenv("XERO_REFRESH_TOKEN")
    XERO_TENANT_ID: str = os.getenv("XERO_TENANT_ID")
    XERO_V2_BASE_URL: str = "https://api.xero.com/api.xro/2.0"
    XERO_TOKEN_URL: str = "https://identity.xero.com/connect/token"

    # default xero user and owner of above credentials
    user_id: str = os.getenv("user_id")
    contact_id: str = os.getenv("contact_id")



config = Settings()
