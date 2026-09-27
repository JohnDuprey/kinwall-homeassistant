"""kinwall.import_recipe and kinwall.plan_meal call the meal planner API and explain failures."""
import pytest
import voluptuous as vol
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kinwall.const import DOMAIN

from .test_setup import BASE_URL, _mock_full_refresh


async def _setup(hass, aioclient_mock):
    _mock_full_refresh(aioclient_mock)
    aioclient_mock.post(f"{BASE_URL}/api/webhooks", json={"id": "wh1"})
    hass.config.internal_url = "http://192.168.1.10:8123"
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_URL: BASE_URL, CONF_API_KEY: "key"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _last_json(aioclient_mock, path):
    return next(call[2] for call in reversed(aioclient_mock.mock_calls) if str(call[1]).endswith(path))


async def test_import_recipe_posts_the_recipe_and_returns_the_result(hass, aioclient_mock):
    await _setup(hass, aioclient_mock)
    result = {"recipeId": "r1", "created": True, "planned": False, "reason": "dinner on 2026-10-05 already has Tacos"}
    aioclient_mock.post(f"{BASE_URL}/api/recipes/import", json=result)
    response = await hass.services.async_call(DOMAIN, "import_recipe", {
        "external_id": "abc", "name": "Creamy Chicken", "servings": 2, "source_url": "https://example.com/card.pdf", "prep_minutes": 10, "total_minutes": 35,
        "ingredients": ["Salt", {"text": "1.5 tablespoon Sour Cream", "pantry": False}], "steps": ["Cook."],
        "plan_date": "2026-10-05", "plan_calendar_id": "cal-1",
    }, blocking=True, return_response=True)
    assert response == result
    assert _last_json(aioclient_mock, "/api/recipes/import") == {
        "source": "hellofresh", "externalId": "abc", "name": "Creamy Chicken", "servings": 2.0, "sourceUrl": "https://example.com/card.pdf", "prepMinutes": 10, "totalMinutes": 35,
        "ingredients": ["Salt", {"text": "1.5 tablespoon Sour Cream", "pantry": False}], "steps": ["Cook."],
        "plan": {"date": "2026-10-05", "slot": "dinner", "calendarId": "cal-1"},
    }
    # Empty (the blueprint's default) means no calendar event.
    aioclient_mock.post(f"{BASE_URL}/api/recipes/import", json=result)
    await hass.services.async_call(DOMAIN, "import_recipe", {"external_id": "abc", "name": "X", "plan_date": "2026-10-05", "plan_calendar_id": ""}, blocking=True, return_response=True)
    assert _last_json(aioclient_mock, "/api/recipes/import")["plan"] == {"date": "2026-10-05", "slot": "dinner"}


async def test_plan_meal_posts_a_meal(hass, aioclient_mock):
    await _setup(hass, aioclient_mock)
    aioclient_mock.post(f"{BASE_URL}/api/meals", json={"id": "m1", "title": "Soup"})
    response = await hass.services.async_call(DOMAIN, "plan_meal", {"date": "2026-10-06", "title": "Soup", "servings": 3}, blocking=True, return_response=True)
    assert response["id"] == "m1"
    assert _last_json(aioclient_mock, "/api/meals") == {"date": "2026-10-06", "slot": "dinner", "title": "Soup", "servings": 3.0, "mealKind": "freeform"}
    aioclient_mock.clear_requests()
    _mock_full_refresh(aioclient_mock)
    aioclient_mock.post(f"{BASE_URL}/api/meals", json={"id": "m2"})
    await hass.services.async_call(DOMAIN, "plan_meal", {"date": "2026-10-07", "slot": "lunch", "recipe_id": "r1"}, blocking=True, return_response=True)
    assert _last_json(aioclient_mock, "/api/meals") == {"date": "2026-10-07", "slot": "lunch", "recipeId": "r1"}
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(DOMAIN, "plan_meal", {"date": "2026-10-07"}, blocking=True, return_response=True)


async def test_display_key_gets_a_clear_error(hass, aioclient_mock):
    await _setup(hass, aioclient_mock)
    aioclient_mock.post(f"{BASE_URL}/api/recipes/import", status=403, json={"error": "display key cannot access this route"})
    with pytest.raises(HomeAssistantError, match="admin key"):
        await hass.services.async_call(DOMAIN, "import_recipe", {"external_id": "abc", "name": "X"}, blocking=True, return_response=True)


async def test_other_api_errors_carry_the_reason(hass, aioclient_mock):
    await _setup(hass, aioclient_mock)
    aioclient_mock.post(f"{BASE_URL}/api/meals", status=400, json={"error": "recipe not found or archived"})
    with pytest.raises(HomeAssistantError, match="recipe not found or archived"):
        await hass.services.async_call(DOMAIN, "plan_meal", {"date": "2026-10-06", "recipe_id": "gone"}, blocking=True, return_response=True)


async def test_unknown_entry_is_rejected(hass, aioclient_mock):
    await _setup(hass, aioclient_mock)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "plan_meal", {"config_entry": "nope", "date": "2026-10-06", "title": "Soup"}, blocking=True, return_response=True)
