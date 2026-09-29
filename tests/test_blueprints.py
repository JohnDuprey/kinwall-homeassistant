"""Blueprints load and produce valid automations; the meal kit import picks the right week and nights."""
from pathlib import Path

import pytest
from homeassistant.components.automation.config import AUTOMATION_BLUEPRINT_SCHEMA, async_validate_config_item
from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
from homeassistant.core import SupportsResponse
from homeassistant.helpers.template import Template
from homeassistant.setup import async_setup_component
from homeassistant.util.yaml import load_yaml

from custom_components.kinwall.services import IMPORT_RECIPE_SCHEMA, SYNC_EVENTS_SCHEMA

@pytest.fixture
def expected_lingering_timers() -> bool:
    """Automations set up here keep their time triggers scheduled after the test."""
    return True


BLUEPRINTS = Path(__file__).parent.parent / "blueprints" / "automation" / "kinwall"
REQUIRED_INPUTS = {
    "reward_switch_bedtime.yaml": {"webhook_id": "abc", "bedtime_entity": "time.switch_bedtime", "moved_today": "input_boolean.moved"},
    "meal_kit_import.yaml": {},
    "meal_kit_deliveries.yaml": {"calendar_id": "cal-1"},
    "night_screen_away.yaml": {},
}


@pytest.mark.parametrize("name", sorted(REQUIRED_INPUTS))
async def test_blueprint_is_a_valid_automation(hass, name):
    blueprint = Blueprint(load_yaml(BLUEPRINTS / name), expected_domain="automation", schema=AUTOMATION_BLUEPRINT_SCHEMA)
    inputs = BlueprintInputs(blueprint, {"use_blueprint": {"path": name, "input": REQUIRED_INPUTS[name]}})
    inputs.validate()
    assert await async_validate_config_item(hass, "test", inputs.async_substitute())


def _meal_kit_templates(name: str = "meal_kit_import.yaml") -> dict[str, str]:
    """Every template in a blueprint's variables steps, by variable name."""
    data = load_yaml(BLUEPRINTS / name)
    found: dict[str, str] = {}

    def walk(steps):
        for step in steps:
            found.update({k: v for k, v in step.get("variables", {}).items() if isinstance(v, str)})
            walk(step.get("repeat", {}).get("sequence", []))
    walk(data["actions"])
    return found


def _render(hass, name: str, **variables):
    return Template(_meal_kit_templates()[name], hass).async_render(variables)


def _week(week_id, delivery, picked=(), skipped=False):
    recipes = [{"recipe_id": f"{week_id}-a", "is_selected": False, "selected_quantity": 0}]
    recipes += [{"recipe_id": rid, "is_selected": True, "selected_quantity": qty} for rid, qty in picked]
    return {"week_id": week_id, "delivery_date": delivery, "is_skipped": skipped, "recipes": recipes}


HF = {"weeks": [
    _week("2026-W38", "2026-09-22", [("old1", 1)]),
    _week("2026-W39", "2026-09-26", [("last1", 1), ("last2", 2)]),
    _week("2026-W40", "2026-09-29", skipped=True, picked=[("skipped", 1)]),
    _week("2026-W41", "2026-10-06", []),  # nothing picked yet
    _week("2026-W42", "2026-10-13", [("next1", 1), ("next2", 2)]),
    {"week_id": "2026-W43", "delivery_date": None, "recipes": []},
]}


async def test_week_selection(hass, freezer):
    freezer.move_to("2026-09-27 10:00:00")
    nxt = _render(hass, "week", hf=HF, which_week="next")
    assert nxt == {"week_id": "2026-W42", "delivery_date": "2026-10-13", "recipes": [{"id": "next1", "quantity": 1}, {"id": "next2", "quantity": 2}]}
    assert _render(hass, "week", hf=HF, which_week="latest")["week_id"] == "2026-W39"
    freezer.move_to("2026-09-26 10:00:00")  # delivery day counts as the next delivery
    assert _render(hass, "week", hf=HF, which_week="next")["week_id"] == "2026-W39"
    assert _render(hass, "week", hf={"weeks": []}, which_week="next") is None
    assert _render(hass, "week", hf=None, which_week="next") is None


async def test_household_servings(hass):
    assert _render(hass, "household_servings", servings_input=4, account={"number_of_people": 2}) == 4
    assert _render(hass, "household_servings", servings_input=0, account={"number_of_people": 2}) == 2
    assert _render(hass, "household_servings", servings_input=0, account={"number_of_people": None}) == 0


async def test_nights(hass):
    week = {"delivery_date": "2026-10-02"}  # a Friday
    assert _render(hass, "nights", week=week, first_night_offset=0, skip_weekends=False) == [
        "2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08"]
    assert _render(hass, "nights", week=week, first_night_offset=1, skip_weekends=True) == [
        "2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09", "2026-10-12", "2026-10-13"]


async def test_ingredient_lines(hass):
    detail = {"recipe": {"ingredients": [
        {"name": "Sour Cream", "amount": 1.5, "unit": "tablespoon", "shipped": True},
        {"name": "Garlic Clove", "amount": 2, "unit": "unit", "shipped": None},
        {"name": "Olive Oil", "amount": 2, "unit": "teaspoon", "shipped": False},
        {"name": "Salt", "amount": None, "unit": "unit", "shipped": False},
        {"name": None, "amount": 1, "unit": "cup"},
    ]}}
    assert _render(hass, "ingredients", detail=detail) == [
        {"text": "1.5 tablespoon Sour Cream", "pantry": False},
        {"text": "2 unit Garlic Clove", "pantry": False},
        {"text": "2 teaspoon Olive Oil", "pantry": True},
        {"text": "Salt", "pantry": True},
    ]


async def test_steps(hass):
    """HelloFresh's instruction lines become bullets; a step photo goes along when the detail has one."""
    detail = {"recipe": {"steps": [
        {"index": 1, "instructions": "Preheat oven to 425 degrees.\nWash produce."},
        {"index": 2, "instructions": "Cook the chicken.", "image_url": "https://img.example/2.jpg"},
        {"index": 3, "instructions": "Toss.\n  \nRoast 15 minutes.", "images": [{"link": "https://img.example/3.jpg", "caption": ""}]},
        {"index": 4, "instructions": "Plate.", "images": ["https://img.example/4.jpg"]},
        {"index": 5, "instructions": "Rest.", "image_url": "http://img.example/5.jpg", "images": []},
        {"index": 6, "instructions": "   "},
        {"index": 7},
        {"index": 8, "instructions": "Roast.", "image_url": None, "caption": " Roast veggies ", "timers": [{"name": "Veggies", "minutes": 20}, {"name": None, "minutes": 5}, {"name": "Bad", "minutes": None}]},
        {"index": 9, "instructions": "Serve.", "caption": None, "timers": []},
    ]}}
    assert _render(hass, "steps", detail=detail) == [
        {"text": "", "bullets": ["Preheat oven to 425 degrees.", "Wash produce."]},
        {"text": "Cook the chicken.", "bullets": [], "image_url": "https://img.example/2.jpg"},
        {"text": "", "bullets": ["Toss.", "Roast 15 minutes."], "image_url": "https://img.example/3.jpg"},
        {"text": "Plate.", "bullets": [], "image_url": "https://img.example/4.jpg"},
        {"text": "Rest.", "bullets": []},  # not https: left off
        {"text": "Roast.", "bullets": [], "title": "Roast veggies", "timers": [{"name": "Veggies", "minutes": 20}, {"name": None, "minutes": 5}]},
        {"text": "Serve.", "bullets": []},
    ]
    assert _render(hass, "steps", detail={"recipe": {"steps": None}}) == []


@pytest.mark.parametrize("calendar_id", [None, "cal-1"])
async def test_meal_kit_import_runs_end_to_end(hass, freezer, calendar_id):
    """Each picked meal lands on the first free night; a taken night moves it to the next.
    With "Add dinners to calendar" set, each import names that calendar."""
    freezer.move_to("2026-09-27 10:00:00")
    details = []

    def respond(result):
        async def handler(call):
            return result(call) if callable(result) else result
        return handler

    def detail(call):
        details.append(dict(call.data))
        rid = call.data["recipe_id"]
        return {"recipe": {"recipe_id": rid, "name": f"Meal {rid}", "headline": "Tasty", "card_url": f"https://example.com/{rid}.pdf",
                           "servings": call.data.get("servings"),
                           "steps": [{"index": 1, "instructions": "Cook.", "caption": "Cook", "timers": [{"name": "Rice", "minutes": 15}]}, {"index": 2, "instructions": "Plate.\nServe.", "image_url": f"https://img.example/{rid}-2.jpg"}],
                           "ingredients": [{"name": "Rice", "amount": 1, "unit": "cup", "shipped": True}]}}

    taken = {"2026-10-13"}  # delivery night already has a dinner
    planned: dict[str, str] = {}
    imports = []

    def import_recipe(call):
        imports.append(dict(call.data))
        rid, night = call.data["external_id"], call.data["plan_date"].isoformat()
        if rid in planned:
            return {"recipeId": rid, "created": False, "planned": True, "mealId": rid}
        if night in taken:
            return {"recipeId": rid, "created": True, "planned": False, "reason": "taken"}
        taken.add(night); planned[rid] = night
        return {"recipeId": rid, "created": True, "planned": True, "mealId": rid}

    only = SupportsResponse.ONLY
    hass.services.async_register("hellofresh", "get_weeks", respond(HF), supports_response=only)
    hass.services.async_register("hellofresh", "get_account_summary", respond({"number_of_people": 2}), supports_response=only)
    hass.services.async_register("hellofresh", "get_recipe_detail", respond(detail), supports_response=only)
    hass.services.async_register("kinwall", "import_recipe", respond(import_recipe), schema=IMPORT_RECIPE_SCHEMA, supports_response=SupportsResponse.OPTIONAL)

    blueprint = Blueprint(load_yaml(BLUEPRINTS / "meal_kit_import.yaml"), expected_domain="automation", schema=AUTOMATION_BLUEPRINT_SCHEMA)
    config = BlueprintInputs(blueprint, {"use_blueprint": {"path": "x", "input": {"calendar_id": calendar_id} if calendar_id else {}}}).async_substitute()
    assert await async_setup_component(hass, "automation", {"automation": [{**config, "id": "kit", "alias": "kit"}]})
    await hass.async_block_till_done()

    async def run():
        await hass.services.async_call("automation", "trigger", {"entity_id": "automation.kit", "skip_condition": True}, blocking=True)
        await hass.async_block_till_done()

    await run()
    assert planned == {"next1": "2026-10-14", "next2": "2026-10-15"}
    assert [d.get("servings") for d in details] == [2, 4]  # the doubled meal is scaled for twice the people
    first = imports[0]
    assert first["source"] == "hellofresh" and first["source_url"] == "https://example.com/next1.pdf" and first["description"] == "Tasty"
    assert first["ingredients"] == [{"text": "1 cup Rice", "pantry": False}] and first["steps"] == [
        {"text": "Cook.", "bullets": [], "title": "Cook", "timers": [{"name": "Rice", "minutes": 15.0}]}, {"text": "", "bullets": ["Plate.", "Serve."], "image_url": "https://img.example/next1-2.jpg"}]
    assert [i["plan_date"].isoformat() for i in imports] == ["2026-10-13", "2026-10-14", "2026-10-13", "2026-10-14", "2026-10-15"]

    assert [i.get("plan_calendar_id") for i in imports] == [calendar_id] * len(imports)  # none unless one is chosen

    imports.clear()
    await run()  # running again finds the meals it planned
    assert [i["plan_date"].isoformat() for i in imports] == ["2026-10-13", "2026-10-13"]
    assert planned == {"next1": "2026-10-14", "next2": "2026-10-15"}


def _delivery_week(week_id, delivery, **extra):
    return {"week_id": week_id, "delivery_date": delivery, "holiday_delivery_date": None, "selection_deadline": None, "slot_label": "Wednesdays: 8AM - 8PM",
            "is_skipped": False, "needs_selection": False, "meals_selected": 0, "meals_required": 3, "recipes": [], **extra}


DELIVERIES = {"weeks": [
    _delivery_week("2026-W39", "2026-09-23", meals_selected=3),  # past: left alone
    _delivery_week("2026-W41", "2026-10-07", selection_deadline="2026-10-02T23:59:59-07:00", needs_selection=True, meals_selected=2, recipes=[
        {"recipe_id": "a", "name": "Creamy Chicken", "is_selected": True}, {"recipe_id": "b", "name": "Tacos", "is_selected": True},
        {"recipe_id": "c", "name": "Not picked", "is_selected": False}, {"recipe_id": "d", "is_selected": True}]),
    _delivery_week("2026-W42", "2026-10-14", is_skipped=True),
    _delivery_week("2026-W43", "2026-10-21", holiday_delivery_date="2026-10-22", slot_label="Thursday", selection_deadline="2026-10-16T09:00:00-04:00", needs_selection=True),
    _delivery_week("2026-W44", "2026-10-28", slot_label="Wednesdays: 9:30 PM - 1 AM", meals_selected=3, selection_deadline="2026-10-23T12:00:00-04:00"),
    _delivery_week("2026-W50", "2026-12-09"),  # beyond the weeks ahead
    {"week_id": "2026-W51", "delivery_date": None},
]}


async def test_delivery_events(hass, freezer):
    await hass.config.async_set_time_zone("America/New_York")
    freezer.move_to("2026-09-28 14:00:00+00:00")
    template = _meal_kit_templates("meal_kit_deliveries.yaml")["events"]
    render = lambda **v: Template(template, hass).async_render({"hf": DELIVERIES, "from_date": "2026-09-28", "to_date": "2026-11-09", "include_deadlines": True, **v})
    assert render() == [
        {"external_id": "delivery-2026-W41", "title": "📦 HelloFresh delivery", "notes": "Creamy Chicken\nTacos\n2 of 3 meals picked",
         "all_day": False, "start": "2026-10-07T08:00:00", "end": "2026-10-07T20:00:00"},
        # 11:59 PM Pacific is 2:59 AM in New York: before 6 AM, so all day on the day before.
        {"external_id": "deadline-2026-W41", "title": "Pick HelloFresh meals", "all_day": True, "start": "2026-10-02", "end": "2026-10-03", "notes": "by 2:59 AM Saturday"},
        {"external_id": "delivery-2026-W43", "title": "📦 HelloFresh delivery", "notes": "0 of 3 meals picked", "all_day": True, "start": "2026-10-22", "end": "2026-10-23"},
        {"external_id": "deadline-2026-W43", "title": "Pick HelloFresh meals", "all_day": False,
         "start": "2026-10-16T08:30:00-04:00", "end": "2026-10-16T09:00:00-04:00", "notes": "by 9:00 AM"},
        {"external_id": "delivery-2026-W44", "title": "📦 HelloFresh delivery", "notes": "3 of 3 meals picked",
         "all_day": False, "start": "2026-10-28T21:30:00", "end": "2026-10-29T01:00:00"},
    ]
    assert [e["external_id"] for e in render(include_deadlines=False)] == ["delivery-2026-W41", "delivery-2026-W43", "delivery-2026-W44"]


async def test_meal_kit_deliveries_runs_end_to_end(hass, freezer):
    """Weeks ahead sets the window; the events go to kinwall.sync_events as the source ha:hellofresh.
    Without weeks from HelloFresh it stops instead of clearing the calendar."""
    await hass.config.async_set_time_zone("America/New_York")
    freezer.move_to("2026-09-28 14:00:00+00:00")
    weeks = {"value": DELIVERIES}
    synced = []

    async def get_weeks(call):
        return weeks["value"]

    async def sync_events(call):
        synced.append(dict(call.data))
        return {"created": 0, "updated": 0, "deleted": 0}

    hass.services.async_register("hellofresh", "get_weeks", get_weeks, supports_response=SupportsResponse.ONLY)
    hass.services.async_register("kinwall", "sync_events", sync_events, schema=SYNC_EVENTS_SCHEMA, supports_response=SupportsResponse.OPTIONAL)
    blueprint = Blueprint(load_yaml(BLUEPRINTS / "meal_kit_deliveries.yaml"), expected_domain="automation", schema=AUTOMATION_BLUEPRINT_SCHEMA)
    config = BlueprintInputs(blueprint, {"use_blueprint": {"path": "x", "input": {"calendar_id": "cal-1", "weeks_ahead": 4}}}).async_substitute()
    assert await async_setup_component(hass, "automation", {"automation": [{**config, "id": "deliveries", "alias": "deliveries"}]})
    await hass.async_block_till_done()

    async def run():
        await hass.services.async_call("automation", "trigger", {"entity_id": "automation.deliveries"}, blocking=True)
        await hass.async_block_till_done()

    await run()
    [call] = synced
    assert (call["calendar_id"], call["source"], call["from"].isoformat(), call["to"].isoformat()) == ("cal-1", "ha:hellofresh", "2026-09-28", "2026-10-26")
    assert [e["external_id"] for e in call["events"]] == ["delivery-2026-W41", "deadline-2026-W41", "delivery-2026-W43", "deadline-2026-W43"]
    assert call["events"][0]["start"].isoformat() == "2026-10-07T08:00:00-04:00"

    weeks["value"] = {"error": "not logged in"}
    await run()
    assert len(synced) == 1


@pytest.mark.parametrize(("state", "away", "home"), [
    ("not_home", True, False), ("Work", True, False), ("home", False, True),  # a person or a group of people
    ("0", True, False), ("2", False, True),  # zone.home counts people
    ("unavailable", False, False), ("unknown", False, False),
])
async def test_night_screen_away_and_home(hass, state, away, home):
    triggers = load_yaml(BLUEPRINTS / "night_screen_away.yaml")["triggers"]
    hass.states.async_set("zone.home", state)
    by_id = {t["id"]: Template(t["value_template"], hass).async_render({"presence": "zone.home"}) for t in triggers}
    assert (by_id["away"], by_id["home"]) == (away, home)
