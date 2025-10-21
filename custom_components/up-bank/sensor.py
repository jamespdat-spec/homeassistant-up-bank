"""Sensors for the Up Bank integration."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, UpDataCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up Up Bank sensors from a config entry."""
    wrapper = hass.data[DOMAIN][entry.entry_id]
    coordinator: UpDataCoordinator = wrapper["coordinator"]

    entities: List[SensorEntity] = []

    # One sensor per account balance
    for acct in coordinator.data.get("accounts", []):
        acct_id = acct.get("id")
        name = (acct.get("attributes") or {}).get("displayName") or f"Up Account {acct_id}"
        if acct_id:
            entities.append(UpAccountBalanceSensor(coordinator, entry, acct_id, name))

    # Summary / total balance sensor
    entities.append(UpTotalBalanceSensor(coordinator, entry))

    # Latest transaction sensors (description/amount/time)
    entities.append(UpLatestTxnDescriptionSensor(coordinator, entry))
    entities.append(UpLatestTxnAmountSensor(coordinator, entry))
    entities.append(UpLatestTxnTimeSensor(coordinator, entry))

    if entities:
        async_add_entities(entities, update_before_add=True)


class _BaseUpSensor(CoordinatorEntity[UpDataCoordinator], SensorEntity):
    """Common bits for Up Bank sensors."""

    _attr_should_poll = False

    def __init__(self, coordinator: UpDataCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Up Bank",
            manufacturer="Up",
        )

    @property
    def available(self) -> bool:
        # Available as long as last update succeeded
        return super().available


class UpAccountBalanceSensor(_BaseUpSensor):
    """Balance sensor for a specific Up account."""

    def __init__(self, coordinator: UpDataCoordinator, entry: ConfigEntry, account_id: str, display_name: str) -> None:
        super().__init__(coordinator, entry)
        self._account_id = account_id
        self._display_name = display_name
        self._attr_name = f"{display_name} Balance"
        self._attr_icon = "mdi:bank"
        # Use the account id in the unique_id so it stays stable
        self._attr_unique_id = f"{entry.entry_id}_acct_{account_id}_balance"
        # Currency unit: Up returns AUD values by default for AU users
        self._attr_native_unit_of_measurement = "AUD"

    @property
    def native_value(self) -> Optional[float]:
        accounts: List[Dict[str, Any]] = self.coordinator.data.get("accounts", [])
        for acct in accounts:
            if acct.get("id") == self._account_id:
                try:
                    return float(acct["attributes"]["balance"]["value"])
                except Exception:
                    return None
        return None


class UpTotalBalanceSensor(_BaseUpSensor):
    """Sum of all account balances."""

    def __init__(self, coordinator: UpDataCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_name = "Up Total Balance"
        self._attr_icon = "mdi:cash-multiple"
        self._attr_unique_id = f"{entry.entry_id}_total_balance"
        self._attr_native_unit_of_measurement = "AUD"

    @property
    def native_value(self) -> Optional[float]:
        summary = self.coordinator.data.get("summary") or {}
        value = summary.get("total_balance")
        try:
            return float(value) if value is not None else None
        except Exception:
            return None


class _LatestTxnBase(_BaseUpSensor):
    """Base class for latest-transaction sensors."""

    def __init__(self, coordinator: UpDataCoordinator, entry: ConfigEntry, name_suffix: str, unique_suffix: str, icon: str) -> None:
        super().__init__(coordinator, entry)
        self._attr_name = f"Up Latest Transaction {name_suffix}"
        self._attr_unique_id = f"{entry.entry_id}_latest_txn_{unique_suffix}"
        self._attr_icon = icon

    @property
    def _latest(self) -> Optional[Dict[str, Any]]:
        txns: List[Dict[str, Any]] = self.coordinator.data.get("transactions", [])
        return txns[0] if txns else None


class UpLatestTxnDescriptionSensor(_LatestTxnBase):
    """Latest transaction description."""

    def __init__(self, coordinator: UpDataCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "Description", "description", "mdi:text")

    @property
    def native_value(self) -> Optional[str]:
        latest = self._latest
        if not latest:
            return None
        return (latest.get("attributes") or {}).get("description")


class UpLatestTxnAmountSensor(_LatestTxnBase):
    """Latest transaction amount (AUD)."""

    def __init__(self, coordinator: UpDataCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "Amount", "amount", "mdi:cash")
        self._attr_native_unit_of_measurement = "AUD"

    @property
    def native_value(self) -> Optional[float]:
        latest = self._latest
        if not latest:
            return None
        try:
            return float(latest["attributes"]["amount"]["value"])
        except Exception:
            return None


class UpLatestTxnTimeSensor(_LatestTxnBase):
    """Latest transaction timestamp (ISO)."""

    def __init__(self, coordinator: UpDataCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "Time", "time", "mdi:clock-outline")

    @property
    def native_value(self) -> Optional[str]:
        latest = self._latest
        if not latest:
            return None
        return (latest.get("attributes") or {}).get("createdAt")
