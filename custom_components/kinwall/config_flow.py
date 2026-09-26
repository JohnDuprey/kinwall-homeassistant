"""Config flow for Kinwall."""
from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KinwallAuthError, KinwallClient
from .const import DEFAULT_CHORE_POINTS, DEFAULT_POLL_INTERVAL, DOMAIN, MAX_POLL_INTERVAL, MIN_POLL_INTERVAL, OPT_CHORE_POINTS, OPT_POLL_INTERVAL

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): str,
        vol.Required(CONF_API_KEY): str,
    }
)


async def _validate(hass, url: str, api_key: str) -> dict[str, Any]:
    """Raise KinwallAuthError/KinwallApiError on failure, else return /api/settings."""
    session = async_get_clientsession(hass)
    client = KinwallClient(session, url, api_key)
    return await client.get_settings()


class KinwallConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a Kinwall config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._reauth_entry: ConfigEntry | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> Any:
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].rstrip("/")
            try:
                settings = await _validate(self.hass, url, user_input[CONF_API_KEY])
            except KinwallAuthError:
                errors = {"base": "invalid_auth"}
            except Exception:  # noqa: BLE001
                errors = {"base": "cannot_connect"}
            else:
                unique_id = urlparse(url).netloc or url
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=settings.get("familyName") or "Kinwall",
                    data={CONF_URL: url, CONF_API_KEY: user_input[CONF_API_KEY]},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
            description_placeholders={"example_url": "http://kinwall.local:8080"},
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> Any:
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> Any:
        errors: dict[str, str] = {}
        assert self._reauth_entry is not None
        if user_input is not None:
            url = self._reauth_entry.data[CONF_URL]
            errors = await self._try_connect(url, user_input[CONF_API_KEY])
            if not errors:
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry,
                    data={**self._reauth_entry.data, CONF_API_KEY: user_input[CONF_API_KEY]},
                )
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    async def _try_connect(self, url: str, api_key: str) -> dict[str, str]:
        try:
            await _validate(self.hass, url, api_key)
        except KinwallAuthError:
            return {"base": "invalid_auth"}
        except Exception:  # noqa: BLE001
            return {"base": "cannot_connect"}
        return {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return KinwallOptionsFlow(config_entry)


class KinwallOptionsFlow(OptionsFlow):
    """Options: poll interval."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> Any:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._config_entry.options.get(OPT_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
        points = self._config_entry.options.get(OPT_CHORE_POINTS, DEFAULT_CHORE_POINTS)
        schema = vol.Schema(
            {
                vol.Optional(OPT_POLL_INTERVAL, default=current): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_POLL_INTERVAL, max=MAX_POLL_INTERVAL)
                ),
                vol.Optional(OPT_CHORE_POINTS, default=points): vol.All(vol.Coerce(int), vol.Range(min=0, max=1000)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
