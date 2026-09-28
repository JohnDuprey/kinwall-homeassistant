"""Actions: import a recipe (e.g. a meal kit's), plan a meal, and sync events into a Kinwall calendar."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util

from .api import KinwallApiError, KinwallAuthError, KinwallClient
from .const import DOMAIN

ATTR_CONFIG_ENTRY = "config_entry"
SLOTS = ["breakfast", "lunch", "dinner", "snack"]

_INGREDIENT = vol.Any(
    cv.string,
    vol.Schema({vol.Required("text"): cv.string, vol.Optional("pantry"): cv.boolean, vol.Optional("category"): vol.Any(None, cv.string)}),
)

_TIMER = vol.Schema({vol.Optional("name"): vol.Any(None, cv.string), vol.Required("minutes"): vol.All(vol.Coerce(float), vol.Range(min=0, min_included=False, max=1440))})

# A step: text (several lines become bullets in Kinwall), or its text, bullets, photo, title
# (caption is the same thing, as HelloFresh calls it) and timers.
_STEP = vol.Any(
    cv.string,
    vol.Schema({
        vol.Optional("text"): vol.Any(None, cv.string), vol.Optional("bullets"): vol.Any(None, [cv.string]), vol.Optional("image_url"): vol.Any(None, cv.url),
        vol.Optional("title"): vol.Any(None, cv.string), vol.Optional("caption"): vol.Any(None, cv.string), vol.Optional("timers"): vol.Any(None, [_TIMER]),
    }),
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
    vol.Optional("prep_minutes"): vol.Any(None, vol.Coerce(int)),
    vol.Optional("total_minutes"): vol.Any(None, vol.Coerce(int)),
    vol.Optional("ingredients", default=list): [_INGREDIENT],
    vol.Optional("steps"): vol.Any(None, [_STEP]),
    vol.Optional("plan_date"): vol.Any(None, cv.date),
    vol.Optional("plan_slot", default="dinner"): vol.In(SLOTS),
    vol.Optional("plan_servings"): vol.Any(None, vol.Coerce(float)),
    vol.Optional("plan_calendar_id"): vol.Any(None, cv.string),
})

def _when(value: Any) -> date | datetime:
    """A date ("2026-10-07") or a date-time (naive ones are Home Assistant's local time)."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=dt_util.get_default_time_zone())
    if isinstance(value, date):
        return value
    text = cv.string(value).strip()
    parsed = dt_util.parse_datetime(text) if ":" in text else dt_util.parse_date(text)
    if parsed is None:
        raise vol.Invalid(f"not a date or date-time: {text}")
    return _when(parsed)


_EVENT = vol.Schema({
    vol.Required("external_id"): cv.string,
    vol.Required("title"): cv.string,
    vol.Required("start"): _when,
    vol.Required("end"): _when,
    vol.Optional("all_day", default=False): cv.boolean,
    vol.Optional("notes"): vol.Any(None, cv.string),
    vol.Optional("location"): vol.Any(None, cv.string),
})

SYNC_EVENTS_SCHEMA = vol.Schema({
    vol.Optional(ATTR_CONFIG_ENTRY): cv.string,
    vol.Required("calendar_id"): cv.string,
    vol.Optional("source", default="home_assistant"): cv.string,
    vol.Optional("from"): vol.Any(None, cv.date),
    vol.Optional("to"): vol.Any(None, cv.date),
    vol.Optional("events", default=list): [_EVENT],
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


def _step(step: str | dict[str, Any]) -> str | dict[str, Any]:
    """A step as Kinwall's import takes it (imageUrl, and no empty fields)."""
    if isinstance(step, str):
        return step
    out = {"text": step.get("text") or "", "bullets": step.get("bullets") or []}
    if step.get("image_url"):
        out["imageUrl"] = step["image_url"]
    if title := step.get("title") or step.get("caption"):
        out["title"] = title
    if step.get("timers"):
        out["timers"] = [{"name": t.get("name"), "minutes": t["minutes"]} for t in step["timers"]]
    return out


async def _import_recipe(call: ServiceCall) -> ServiceResponse:
    d = call.data
    payload: dict[str, Any] = {"source": d["source"], "externalId": d["external_id"], "name": d["name"], "ingredients": d["ingredients"]}
    for key, api_key in (("description", "description"), ("source_url", "sourceUrl"), ("image_url", "imageUrl"), ("servings", "servings"), ("prep_minutes", "prepMinutes"), ("total_minutes", "totalMinutes")):
        if d.get(key) is not None:
            payload[api_key] = d[key]
    if d.get("steps") is not None:
        payload["steps"] = [_step(s) for s in d["steps"]]
    if d.get("plan_date") is not None:
        payload["plan"] = {"date": d["plan_date"].isoformat(), "slot": d["plan_slot"]}
        if d.get("plan_servings") is not None:
            payload["plan"]["servings"] = d["plan_servings"]
        if d.get("plan_calendar_id"):  # empty = no calendar event
            payload["plan"]["calendarId"] = d["plan_calendar_id"]
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


def _iso(value: date | datetime, all_day: bool) -> str:
    """All-day events as dates; timed ones as date-times with their offset."""
    if all_day:
        return (value.date() if isinstance(value, datetime) else value).isoformat()
    if not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time(), dt_util.get_default_time_zone())
    return value.isoformat()


async def _sync_events(call: ServiceCall) -> ServiceResponse:
    d = call.data
    payload: dict[str, Any] = {"source": d["source"]}
    for key in ("from", "to"):
        if d.get(key) is not None:
            payload[key] = d[key].isoformat()
    events = []
    for e in d["events"]:
        event = {"externalId": e["external_id"], "title": e["title"], "start": _iso(e["start"], e["all_day"]), "end": _iso(e["end"], e["all_day"]), "allDay": e["all_day"]}
        for key in ("notes", "location"):
            if e.get(key):
                event[key] = e[key]
        events.append(event)
    payload["events"] = events
    return await _call("sync the events", _client(call.hass, call).sync_events(d["calendar_id"], payload))


def async_setup_services(hass: HomeAssistant) -> None:
    hass.services.async_register(DOMAIN, "import_recipe", _import_recipe, schema=IMPORT_RECIPE_SCHEMA, supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, "sync_events", _sync_events, schema=SYNC_EVENTS_SCHEMA, supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, "plan_meal", _plan_meal, schema=PLAN_MEAL_SCHEMA, supports_response=SupportsResponse.OPTIONAL)
