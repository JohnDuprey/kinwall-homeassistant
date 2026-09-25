"""Config flow tests: happy path + invalid auth."""
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.data_entry_flow import FlowResultType

from custom_components.kinwall.const import DOMAIN

BASE_URL = "http://kinwall.local:8080"


async def test_user_flow_success(hass, aioclient_mock):
    aioclient_mock.get(
        f"{BASE_URL}/api/settings",
        json={"familyName": "The Parkers", "timezone": "UTC", "weekStart": 0, "theme": "light"},
    )

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: BASE_URL, CONF_API_KEY: "fc_goodkey"}
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "The Parkers"
    assert result2["data"] == {CONF_URL: BASE_URL, CONF_API_KEY: "fc_goodkey"}


async def test_user_flow_invalid_auth(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}/api/settings", status=401)

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: BASE_URL, CONF_API_KEY: "fc_badkey"}
    )
    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_user_flow_cannot_connect(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}/api/settings", exc=Exception("boom"))

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: BASE_URL, CONF_API_KEY: "fc_key"}
    )
    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}

