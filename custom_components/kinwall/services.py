"""Actions: import a recipe (e.g. a meal kit's) and plan a meal on Kinwall's meal planner."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .api import KinwallApiError, KinwallAuthError, KinwallClient
from .const import DOMAIN

ATTR_CONFIG_ENTRY = "config_entry"
SLOTS = ["breakfast", "lunch", "dinner", "snack"]

_INGREDIENT = vol.Any(
    cv.string,
    vol.Schema({vol.Required("text"): cv.string, vol.Optional("pantry"): cv.boolean, vol.Optional("category"): vol.Any(None, cv.string)}),
)

IMPORT_RECIPE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_CONFIG_ENTRY): cv.string,
    vol.Optional("source", default="hellofresh"): cv.string,
    vol.Required("external_id"): cv.string,
    vol.Required("name"): cv.string,
    vol.Optional("description"): vol.Any(None, cv.string),
    vol.Optional("source_url"): vol.Any(None, cv.url),
    vol.Optional("image_url"): vol.Any(None, cv.url),
    vol.Optional("servings"): vol.Any(None, vol.Coerce(float)),
    vol.Optional("ingredients", default=list): [_INGREDIENT],
    vol.Optional("steps"): vol.Any(None, [cv.string]),
    vol.Optional("plan_date"): vol.Any(None, cv.date),
    vol.Optional("plan_slot", default="dinner"): vol.In(SLOTS),
    vol.Optional("plan_servings"): vol.Any(None, vol.Coerce(float)),
})

PLAN_MEAL_SCHEMA = vol.All(
    vol.Schema({
        vol.Optional(ATTR_CONFIG_ENTRY): cv.string,
        vol.Required("date"): cv.date,
        vol.Optional("slot", default="dinner"): vol.In(SLOTS),
        vol.Optional("title"): cv.string,
        vol.Optional("recipe_id"): cv.string,
        vol.Optional("servings"): vol.Coerce(float),
        vol.Optional("notes"): cv.string,
    }),
    cv.has_at_least_one_key("title", "recipe_id"),
)


def _client(hass: HomeAssistant, call: ServiceCall) -> KinwallClient:
    """The client of the chosen entry, or of the only loaded one."""
    entries = [e for e in hass.config_entries.async_entries(DOMAIN) if e.state is ConfigEntryState.LOADED]
    wanted = call.data.get(ATTR_CONFIG_ENTRY)
    if wanted:
        entries = [e for e in entries if e.entry_id == wanted]
        if not entries:
            raise ServiceValidationError(f"No loaded Kinwall entry with id {wanted}")
    elif len(entries) != 1:
        raise ServiceValidationError(
            "No Kinwall entry is loaded" if not entries else "More than one Kinwall is set up: choose one with config_entry"
        )
    return hass.data[DOMAIN][entries[0].entry_id].client


async def _call(what: str, request) -> Any:
    """Turn API failures into errors an automation's trace explains."""
    try:
        return await request
    except KinwallAuthError as err:
        raise HomeAssistantError(f"Kinwall rejected the API key while trying to {what}; reauthenticate the integration") from err
    except KinwallApiError as err:
        if err.status == 403:
            raise HomeAssistantError(
                f"Kinwall refused to {what}: the integration's API key is a display key. "
                "The meal planner needs an admin key (Kinwall Settings → Access → API keys); reconfigure the integration with one."
            ) from err
        raise HomeAssistantError(f"Kinwall could not {what}: {err.reason or err}") from err


async def _import_recipe(call: ServiceCall) -> ServiceResponse:
    d = call.data
    payload: dict[str, Any] = {"source": d["source"], "externalId": d["external_id"], "name": d["name"], "ingredients": d["ingredients"]}
    for key, api_key in (("description", "description"), ("source_url", "sourceUrl"), ("image_url", "imageUrl"), ("servings", "servings"), ("steps", "steps")):
        if d.get(key) is not None:
            payload[api_key] = d[key]
    if d.get("plan_date") is not None:
        payload["plan"] = {"date": d["plan_date"].isoformat(), "slot": d["plan_slot"]}
        if d.get("plan_servings") is not None:
            payload["plan"]["servings"] = d["plan_servings"]
    return await _call("import the recipe", _client(call.hass, call).import_recipe(payload))


async def _plan_meal(call: ServiceCall) -> ServiceResponse:
    d = call.data
    payload: dict[str, Any] = {"date": d["date"].isoformat(), "slot": d["slot"]}
    for key, api_key in (("title", "title"), ("recipe_id", "recipeId"), ("servings", "servings"), ("notes", "notes")):
        if d.get(key) is not None:
            payload[api_key] = d[key]
    if "recipe_id" not in d:
        payload["mealKind"] = "freeform"
    return await _call("plan the meal", _client(call.hass, call).create_meal(payload))


def async_setup_services(hass: HomeAssistant) -> None:
    hass.services.async_register(DOMAIN, "import_recipe", _import_recipe, schema=IMPORT_RECIPE_SCHEMA, supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, "plan_meal", _plan_meal, schema=PLAN_MEAL_SCHEMA, supports_response=SupportsResponse.OPTIONAL)
