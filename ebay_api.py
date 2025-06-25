import os
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()


class EbayAPI:
    def __init__(self, env="PROD"):
        self.env = env.upper()

        if self.env == "SANDBOX":
            self.client_id = os.getenv("SANDBOX_CLIENT_ID")
            self.client_secret = os.getenv("SANDBOX_CLIENT_SECRET")
            self.auth_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
            self.api_url = "https://api.sandbox.ebay.com"
        elif self.env == "PROD":
            self.client_id = os.getenv("PROD_CLIENT_ID")
            self.client_secret = os.getenv("PROD_CLIENT_SECRET")
            self.auth_url = "https://api.ebay.com/identity/v1/oauth2/token"
            self.api_url = "https://api.ebay.com"
        else:
            raise ValueError("envは 'SANDBOX' または 'PROD' を指定してください。")

        self.scope = os.getenv("EBAY_SCOPE", "https://api.ebay.com/oauth/api_scope/buy.marketplace.insights")
        self.access_token = self.get_access_token()

    def get_access_token(self):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'grant_type': 'client_credentials',
            'scope': self.scope
        }

        response = requests.post(
            self.auth_url,
            headers=headers,
            data=data,
            auth=HTTPBasicAuth(self.client_id, self.client_secret)
        )

        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            raise Exception(f"認証エラー: {response.status_code} {response.text}")

    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }
