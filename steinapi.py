import httpx
import logging
import time

class SteinAPI:
    """Holds the connection to THW stein.app"""

    baseurl = "https://stein.app/api/api/ext"

    def __init__(self, bu_id: int, api_key: str) -> None:
        """Initialize with the business unit ID and API key."""
        self.bu_id = bu_id
        self.session = httpx.Client(http2=True, headers={
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json',
            'Authorization': f'Bearer {api_key}'  # use Bearer token format
        })
        self.last_request_time = 0

    def _rate_limit(self):
        """Ensure we don't exceed the rate limit of 20 requests per minute."""
        current_time = time.time()
        elapsed_time = current_time - self.last_request_time
        if elapsed_time < 3:  # 60 seconds / 20 requests = 3 seconds per request
            time.sleep(3 - elapsed_time)
        self.last_request_time = time.time()

    def get_assets(self) -> dict:
        """Fetch assets for the business unit."""
        self._rate_limit()
        url = f"{self.baseurl}/assets/?buIds={self.bu_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def update_asset(self, asset_id: int, update_data: dict, notify: bool = False) -> bool:
        """Update an asset with the provided data."""
        self._rate_limit()
        url = f"{self.baseurl}/assets/{asset_id}"
        params = {'notifyRadio': str(notify).lower()}
        response = self.session.patch(url, json=update_data, params=params)
        if response.status_code == 200:
            return True
        else:
            logging.warning(f"Failed to update asset {asset_id}: {response.text}")
            return False
