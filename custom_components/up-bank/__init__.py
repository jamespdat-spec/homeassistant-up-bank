"""Up Bank integration bootstrap."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_API_KEY
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

# IMPORTANT:
# The domain must match the integration folder name (this repo uses "up-bank").
DOMAIN = "up-bank"
PLATFORMS = ["sensor"]

_LOGGER = logging.getLogger(__name__)

API_BASE = "https://api.up.com.au/api/v1"


class UpApi:
    """Tiny async client for the Up API using HA's shared session."""

    def __init__(self, hass: HomeAssistant, token: str) -> None:
        self._session = async_get_clientsession(hass)
        self._headers = {"Authorization": f"Bearer {token}"}

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{API_BASE}{path}"
        async with self._session.get(url, headers=self._headers, params=params) as resp:
            if resp.status == 401:
                text = await resp.text()
                raise UpdateFailed(f"Unauthorized (401). Check your Up API token. Body: {text[:200]}")
            if resp.status >= 400:
                text = await resp.text()
                raise UpdateFailed(f"Up API error {resp.status}: {text[:200]}")
            return await resp.json()

    async def get_accounts(self) -> Dict[str, Any]:
        # Returns a dict with "data": [ ... accounts ... ]
        return await self._get("/accounts")

    async def get_transactions(self, page_size: int = 50) -> Dict[str, Any]:
        # Most recent first
        return await self._get("/transactions", params={"page[size]": str(page_size)})


class UpDataCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Coordinator that fetches accounts and recent transactions."""

    def __init__(self, hass: HomeAssistant, api: UpApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Up Bank Coordinator",
            update_interval=timedelta(minutes=10),  # adjust as you like
        )
        self.api = api

    async def _async_update_data(self) -> Dict[str, Any]:
        # Fetch both endpoints; if either fails, raise UpdateFailed to let HA retry.
        accounts = await self.api.get_accounts()
        txns = await self.api.get_transactions(page_size=50)

        # Normalize a tiny bit so sensors have a stable structure.
        accounts_list = accounts.get("data") or []
        txns_list = txns.get("data") or []

        # Build a summary to avoid repeating template code in sensor.py
        try:
            total_balance = sum(
                float(acct["attributes"]["balance"]["value"])
                for acct in accounts_list
                if "attributes" in acct and "balance" in acct["attributes"]
            )
        except Exception as exc:
            raise UpdateFailed(f"Failed to compute total balance: {exc}") from exc

        data: Dict[str, Any] = {
            "accounts": accounts_list,
            "transactions": txns_list,
            "summary": {"total_balance": total_balance},
        }
        return data


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Up Bank from a config entry."""
    token = entry.data.get(CONF_API_KEY)
    if not token:
        # Some forks used a different key name; try a fallback
        token = entry.data.get("token") or entry.data.get("api_key")

    if not token:
        raise ConfigEntryNotReady("No API token found in config entry")

    api = UpApi(hass, token)
    coordinator = UpDataCoordinator(hass, api)

    # Make sure the very first refresh completes BEFORE we forward to platforms.
    await coordinator.async_config_entry_first_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady("Initial Up API fetch failed")

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.debug("Up Bank setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Up Bank config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
