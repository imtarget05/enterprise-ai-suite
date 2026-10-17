"""
Salesforce REST API Integration Adapter.
Provides OAuth 2.0 Client Credentials flow, Account sync, external ID mapping,
and retry with exponential backoff.
"""

import asyncio
from typing import Any, Dict, Optional
import httpx


class SalesforceAdapter:
    def __init__(
        self,
        auth_url: str = "https://login.salesforce.com/services/oauth2/token",
        instance_url: str = "https://enterprise-demo.my.salesforce.com",
        client_id: str = "demo_sf_client_id",
        client_secret: str = "demo_sf_client_secret",
        username: str = "developer@enterprise.demo",
        password: str = "demo_sf_password",
        use_sandbox: bool = True,
    ):
        self.auth_url = auth_url
        self.instance_url = instance_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.use_sandbox = use_sandbox
        self.access_token: Optional[str] = None
        self._accounts = {
            "0018b00002ABC01": {
                "Id": "0018b00002ABC01",
                "Name": "Acme Manufacturing Corp",
                "ERP_External_ID__c": "CUST-ACME-01",
                "AnnualRevenue": 5000000.0,
                "Industry": "Manufacturing",
                "Rating": "Hot",
                "LastModifiedDate": "2026-10-15T12:00:00.000Z",
            }
        }

    async def authenticate(self) -> str:
        if self.use_sandbox:
            self.access_token = "mock_salesforce_access_token_dev_edition"
            return self.access_token

        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(self.auth_url, data=payload)
            resp.raise_for_status()
            self.access_token = resp.json().get("access_token")
            return self.access_token

    async def get_account_by_external_id(self, external_id: str, retries: int = 3) -> Optional[Dict[str, Any]]:
        if self.use_sandbox:
            for acc in self._accounts.values():
                if acc.get("ERP_External_ID__c") == external_id:
                    return acc
            return None

        if not self.access_token:
            await self.authenticate()

        url = f"{self.instance_url}/services/data/v60.0/sobjects/Account/ERP_External_ID__c/{external_id}"
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.get(url, headers=headers)
                    if resp.status_code == 404:
                        return None
                    resp.raise_for_status()
                    return resp.json()
            except httpx.HTTPError:
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
        return None


salesforce_adapter = SalesforceAdapter()
