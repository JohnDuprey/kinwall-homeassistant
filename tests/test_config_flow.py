"""Config flow tests: happy path + invalid auth."""
from aiohttp import ClientError
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
    aioclient_mock.get(f"{BASE_URL}/api/settings", exc=ClientError("boom"))

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: BASE_URL, CONF_API_KEY: "fc_key"}
    )
    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}



def _mock_full_refresh(aioclient_mock, rev_status: int = 200):
    aioclient_mock.get(f"{BASE_URL}/api/rev", json={"rev": 1}, status=rev_status)
    aioclient_mock.get(f"{BASE_URL}/api/settings", json={})
    aioclient_mock.get(f"{BASE_URL}/api/members", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/calendars", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/events", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/chores", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/chores/day", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/lists", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/displays/night-screen", status=404)
    aioclient_mock.post(f"{BASE_URL}/api/webhooks", json={"id": "wh1"})


def _setups(aioclient_mock) -> int:
    """Each setup's first refresh reads the members once."""
    return sum(1 for m, u, *_ in aioclient_mock.mock_calls if m == "GET" and u.path == "/api/members")


async def _reauth(hass, entry):
    result = await entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_API_KEY: "fc_newkey"})
    await hass.async_block_till_done()
    return result


async def test_reauth_of_a_loaded_entry_reloads_it_once(hass, aioclient_mock):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    _mock_full_refresh(aioclient_mock)
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_URL: BASE_URL, CONF_API_KEY: "fc_oldkey"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert _setups(aioclient_mock) == 1

    result = await _reauth(hass, entry)
    assert result["type"] == FlowResultType.ABORT and result["reason"] == "reauth_successful"
    assert entry.data[CONF_API_KEY] == "fc_newkey"
    assert _setups(aioclient_mock) == 2  # the update listener's reload, and no second one


async def test_reauth_of_an_entry_that_failed_setup_loads_it(hass, aioclient_mock):
    from homeassistant.config_entries import ConfigEntryState
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    _mock_full_refresh(aioclient_mock, rev_status=401)
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_URL: BASE_URL, CONF_API_KEY: "fc_oldkey"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR

    aioclient_mock.clear_requests()
    _mock_full_refresh(aioclient_mock)
    await _reauth(hass, entry)
    assert entry.state is ConfigEntryState.LOADED


async def test_user_flow_unknown_error(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}/api/settings", exc=Exception("boom"))

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: BASE_URL, CONF_API_KEY: "fc_key"}
    )
    assert result2["errors"] == {"base": "unknown"}


async def test_user_flow_adds_missing_scheme(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}/api/settings", json={"familyName": "The Parkers"})

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: "kinwall.local:8080/", CONF_API_KEY: "fc_goodkey"}
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["data"][CONF_URL] == BASE_URL


async def test_user_flow_invalid_url(hass):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: "http://", CONF_API_KEY: "fc_key"}
    )
    assert result2["errors"] == {"base": "invalid_url"}
