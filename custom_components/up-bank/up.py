import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)
#_LOGGER.setLevel(logging.DEBUG)  # Ensure debug-level messages are logged

BASE_URL = "https://api.up.com.au/api/v1"

class UP:
    def __init__(self, api_key):
        self.api_key = api_key

    async def call(self, endpoint, params=None, method="get"):
        if params is None:
            params = {}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        _LOGGER.debug(f"Making {method.upper()} request to {BASE_URL + endpoint} with headers: {headers} and params: {params}")
        
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.request(method, BASE_URL + endpoint, params=params) as resp:
                    _LOGGER.debug(f"Received response status: {resp.status}")
                    
                    if resp.status == 401:
                        _LOGGER.error("Unauthorized: Invalid API Key")
                        return None
                    if resp.status != 200:
                        _LOGGER.error(f"Error: Received status code {resp.status}")
                        return None
                    
                    response_data = await resp.json()
                    _LOGGER.debug(f"Response JSON: {response_data}")
                    return response_data
            except aiohttp.ClientError as e:
                _LOGGER.error(f"Network error occurred: {e}")
                return None

    async def test(self, api_key=None) -> bool:
        original_key = self.api_key
        if api_key:
            self.api_key = api_key
        
        try:
            result = await self.call("/util/ping")
            if result is not None:
                _LOGGER.debug("API key validated successfully.")
                return True
            else:
                _LOGGER.error("API key validation failed.")
                return False
        finally:
            self.api_key = original_key

    async def get_accounts(self):
        result = await self.call('/accounts', {"page[size]": 100})
        if result is None:
            _LOGGER.warning("Failed to retrieve accounts.")
            return None

        accounts = {}
        for account in result.get('data', []):
            details = BankAccount(account)
            accounts[details.id] = details
        _LOGGER.debug(f"Retrieved accounts: {accounts}")
        return accounts

class BankAccount:
    def __init__(self, data):
        self.name = data['attributes']['displayName']
        self.balance = data['attributes']['balance']['value']
        self.id = data['id']
        self.created_at = data['attributes']['createdAt']
        self.account_type = data['attributes']['accountType']
        self.ownership = data['attributes']['ownershipType']
