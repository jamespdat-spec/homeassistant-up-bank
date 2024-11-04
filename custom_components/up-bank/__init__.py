import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .up import UP
from .const import DOMAIN, PLATFORMS, CONF_API_KEY  # Ensure constants are defined

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]  # Define platforms for easier reference

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Up Bank from a config entry."""
    
    # Initialize the UP instance with the API key
    api_key = entry.data[CONF_API_KEY]
    up_bank_instance = UP(api_key)

    # Test the API connection to ensure readiness
    try:
        if not await up_bank_instance.test():
            _LOGGER.error("Up Bank API not ready. Retrying later.")
            raise ConfigEntryNotReady
    except Exception as err:
        _LOGGER.error("Unexpected error during setup: %s", err)
        raise ConfigEntryNotReady from err

    # Store the instance and forward the entry setup to specified platforms
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = up_bank_instance
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    
    # Unload platforms for the integration
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    # Remove instance data if unload was successful
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

