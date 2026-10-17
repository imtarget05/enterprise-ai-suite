"""
Salesforce REST API Integration Adapter.
Provides OAuth 2.0 Client Credentials flow, Account / Lead / Opportunity sync,
external ID mapping (ERP_External_ID__c), SOQL querying, and retry with exponential backoff.
"""

import asyncio
from typing import Any, Dict, List, Optional
import urllib.parse
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

        self._leads = {
            "00Q8b00001XYZ01": {
                "Id": "00Q8b00001XYZ01",
                "Name": "Sarah Jenkins",
                "Company": "Acme Manufacturing Corp",
                "Email": "sjenkins@acmefab.com",
                "Status": "Working - Contacted",
                "ERP_External_ID__c": "LEAD-ACME-01",
                "CreatedDate": "2026-10-10T09:00:00.000Z",
            },
            "00Q8b00001XYZ02": {
                "Id": "00Q8b00001XYZ02",
                "Name": "David Chen",
                "Company": "Global Tech Aerospace",
                "Email": "dchen@globaltech.com",
                "Status": "Open - Not Contacted",
                "ERP_External_ID__c": "LEAD-GTA-02",
                "CreatedDate": "2026-10-14T14:30:00.000Z",
            },
        }

        self._opportunities = {
            "0068b00002OPP01": {
                "Id": "0068b00002OPP01",
                "Name": "Acme CNC Aluminum Order Q4",
                "AccountId": "0018b00002ABC01",
                "Amount": 12500.0,
                "StageName": "Proposal/Price Quote",
                "Probability": 80,
                "CloseDate": "2026-11-15",
                "ERP_External_ID__c": "OPP-ACME-01",
                "LastModifiedDate": "2026-10-16T10:15:00.000Z",
            },
            "0068b00002OPP02": {
                "Id": "0068b00002OPP02",
                "Name": "Global Tech Titanium Fasteners",
                "AccountId": "0018b00002DEF02",
                "Amount": 45000.0,
                "StageName": "Negotiation/Review",
                "Probability": 90,
                "CloseDate": "2026-12-01",
                "ERP_External_ID__c": "OPP-GTA-02",
                "LastModifiedDate": "2026-10-17T08:00:00.000Z",
            },
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

    async def get_lead_by_external_id(self, external_id: str, retries: int = 3) -> Optional[Dict[str, Any]]:
        """Lookup Salesforce Lead by external ERP identifier."""
        if self.use_sandbox:
            for lead in self._leads.values():
                if lead.get("ERP_External_ID__c") == external_id:
                    return lead
            return None

        if not self.access_token:
            await self.authenticate()

        url = f"{self.instance_url}/services/data/v60.0/sobjects/Lead/ERP_External_ID__c/{external_id}"
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

    async def query_leads(
        self,
        company: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Query Salesforce Leads with optional company/status filters."""
        if self.use_sandbox:
            results = []
            for lead in self._leads.values():
                if company and company.lower() not in lead.get("Company", "").lower():
                    continue
                if status and status.lower() != lead.get("Status", "").lower():
                    continue
                results.append(lead)
            return results[:limit]

        if not self.access_token:
            await self.authenticate()

        where_clauses = []
        if company:
            where_clauses.append(f"Company LIKE '%{company}%'")
        if status:
            where_clauses.append(f"Status = '{status}'")
        where_str = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        soql = f"SELECT Id, Name, Company, Email, Status, ERP_External_ID__c, CreatedDate FROM Lead{where_str} LIMIT {limit}"
        return await self.query_soql(soql)

    async def get_opportunity_by_external_id(self, external_id: str, retries: int = 3) -> Optional[Dict[str, Any]]:
        """Lookup Salesforce Opportunity by external ERP identifier."""
        if self.use_sandbox:
            for opp in self._opportunities.values():
                if opp.get("ERP_External_ID__c") == external_id:
                    return opp
            return None

        if not self.access_token:
            await self.authenticate()

        url = f"{self.instance_url}/services/data/v60.0/sobjects/Opportunity/ERP_External_ID__c/{external_id}"
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

    async def query_opportunities(
        self,
        account_id: Optional[str] = None,
        stage_name: Optional[str] = None,
        min_amount: Optional[float] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Query Salesforce Opportunities with optional filters."""
        if self.use_sandbox:
            results = []
            for opp in self._opportunities.values():
                if account_id and opp.get("AccountId") != account_id:
                    continue
                if stage_name and stage_name.lower() != opp.get("StageName", "").lower():
                    continue
                if min_amount is not None and opp.get("Amount", 0.0) < min_amount:
                    continue
                results.append(opp)
            return results[:limit]

        if not self.access_token:
            await self.authenticate()

        where_clauses = []
        if account_id:
            where_clauses.append(f"AccountId = '{account_id}'")
        if stage_name:
            where_clauses.append(f"StageName = '{stage_name}'")
        if min_amount is not None:
            where_clauses.append(f"Amount >= {min_amount}")
        where_str = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        soql = f"SELECT Id, Name, AccountId, Amount, StageName, Probability, CloseDate, ERP_External_ID__c FROM Opportunity{where_str} LIMIT {limit}"
        return await self.query_soql(soql)

    async def query_soql(self, soql: str, retries: int = 3) -> List[Dict[str, Any]]:
        """Execute arbitrary SOQL query with retry backoff."""
        if self.use_sandbox:
            return list(self._opportunities.values())

        if not self.access_token:
            await self.authenticate()

        encoded_query = urllib.parse.quote(soql)
        url = f"{self.instance_url}/services/data/v60.0/query/?q={encoded_query}"
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(url, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                    return data.get("records", [])
            except httpx.HTTPError:
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
        return []


salesforce_adapter = SalesforceAdapter()
