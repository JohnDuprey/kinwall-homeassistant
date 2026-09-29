# Kinwall for Home Assistant

Home Assistant integration and add-on for [Kinwall](https://github.com/JohnDuprey/kinwall), a
self-hosted, open-source family wall calendar + chore chart. The main Kinwall server lives in a
separate repo; this repo has:

- **`custom_components/kinwall`** — a HACS-installable integration: calendars, to-do lists, and
  sensors for each family member, and Night screen switches for the wall screens, kept live via a
  push webhook.
- **`kinwall/`** — a Home Assistant add-on that runs the Kinwall server itself.

## Install the integration (HACS)

1. HACS → Integrations → ⋮ → Custom repositories → add
   `https://github.com/JohnDuprey/kinwall-homeassistant`, category "Integration".
2. Install "Kinwall", restart Home Assistant.
3. Settings → Devices & Services → Add Integration → "Kinwall".
4. Enter your Kinwall URL and an **admin**-scope API key (Settings → API keys in Kinwall). Admin
   scope is required once, to register the push webhook; day-to-day polling and writes only need the
   key you provided.

## Install the add-on

Settings → Add-ons → Add-on Store → ⋮ → Repositories → add
`https://github.com/JohnDuprey/kinwall-homeassistant`, then install "Kinwall" from the store. See
[`kinwall/DOCS.md`](kinwall/DOCS.md) for configuration and iPad kiosk setup.

## Configuration

- **URL / API key**: set during setup; the API key can be replaced later via the reauth flow if it's
  revoked or rotated.
- **Points for chores created from Home Assistant** (integration Options, default 5): every chore added from an HA to-do list or an automation (`todo.add_item`) gets this many points.
- **Poll interval** (integration Options, default 30s): how often the integration checks
  `GET /api/rev`. Real-time updates don't depend on this — the integration also registers a Kinwall
  webhook and refreshes immediately when the server pushes a change.

## Entities

One device per family member, plus a "Family" device for shared/aggregate entities, and one per
paired wall screen.

| Entity | Device | Description |
|---|---|---|
| `calendar.<member>` | Member | That member's events (any calendar where `memberIds` includes them). Supports creating/editing/deleting events on their first writable calendar. |
| `calendar.family` | Family | Read-only, all members' events merged. |
| `todo.<member>` | Member | That day's chores assigned to them. Checking an item off calls Kinwall's complete endpoint; unchecking undoes it. Adding an item creates a one-off chore due today. |
| `todo.anyone` | Family | Unassigned chores due today. |
| `todo.<list>` | Family | One entity per Kinwall list (shopping/to-do/reusable) — see [Lists](#lists) below. |
| `sensor.<member>_points_today` | Member | Chore points earned today. |
| `sensor.<member>_points_this_week` | Member | Chore points earned this (household-timezone) week. |
| `sensor.<member>_chores_remaining_today` | Member | Count of today's chores not yet completed. |
| `binary_sensor.<member>_<chore>` | Member (or Family for unassigned) | One per chore: **on** once it's completed today, off while open or not due today. Attributes: `due_today`, `points`, `completed_at`, and `checklist` / `checklist_done` / `checklist_total` when the chore has a checklist. The thing to gate automations on ("is the after-school checklist done?"). New chores appear after reloading the integration. |
| `switch.family_night_screen` | Family | The [Night screen](#night-screen) on every wall screen. |
| `switch.<display>_night_screen` | Wall screen | The Night screen on one paired display. |

### Lists

Every non-archived Kinwall list (shopping, to-do, or reusable) shows up as its own `todo.*` entity,
added or removed automatically as lists are created, deleted, or archived. This is what lets voice
assistants and the Lovelace to-do card work directly against Kinwall lists — e.g. *"Hey Google, add
milk to the groceries list."*

Field mapping (`ListItem` → `TodoItem`):

| Kinwall `ListItem` | `TodoItem` |
|---|---|
| `id` | `uid` |
| `title` | `summary` |
| `done` | `status` (`COMPLETED` / `NEEDS_ACTION`) |
| `dueDate` | `due` |
| `notes`, plus `store`/`category`/`quantity` on shopping lists as a generated "Store · Category · qty" line | `description` |

Creating an item only sends the title (and due date/notes if you gave them), so the server's
"remember the store/category I last used for this title" behavior kicks in. Editing the description
only ever writes back your own notes — the generated store/category line is stripped out, never
overwritten.

### Events

The integration fires `kinwall_<type>` on the Home Assistant event bus for every Kinwall webhook it
receives (e.g. `kinwall_chore_completed`, `kinwall_events_changed`), with the webhook's `data` payload
as the event data — use these in automations for anything the built-in entities don't cover directly.

### Night screen

Needs a Kinwall server newer than 1.1.0 (with an older one, or a display key, the switches just
don't appear). The Night screen switches start the Night screen on Kinwall's wall screens and end
it again, the same as the moon button on the wall: each wall uses its own Night screen settings and
stays awake. **Family → Night screen** covers every wall screen, including devices with **Use as a
wall screen** on; each paired display also gets its own device with a Night screen switch. Turning
the Family switch on or off resets the per-screen ones.

* Walls start it within 30 seconds and wake within about 10 seconds of the switch going off.
* A tap on a wall still wakes it (the quiet-hours PIN only during quiet hours). It stays awake until
  the switch changes again or quiet hours start.
* "On" runs out on its own after 12 hours, and the switch goes off then too. Use
  `kinwall.night_screen` with `hours` for longer.
* Wall screens paired after setup appear after reloading the integration.

### Actions

All four need the integration's API key to be an **admin** key (a display key gets a clear error). With more than one Kinwall set up, pick one with `config_entry`. Each returns Kinwall's answer (`response_variable`).

| Action | What it does |
|---|---|
| `kinwall.import_recipe` | Adds a recipe to Kinwall's recipe library from another app, such as a meal kit, or updates it when the same `source` + `external_id` was imported before. Fields: `source` (default `hellofresh`), `external_id`, `name`, `description`, `source_url` (recipe card), `image_url`, `servings` (what the amounts are for), `ingredients` (lines like `"1.5 tablespoon Sour Cream"`, or `{text, pantry, category}` where `pantry: false` means it ships in the kit and stays off grocery lists), `steps` (text, or `{text, bullets, image_url, title, timers}` with the step's short instructions, photo, a short heading (`caption` works too) and timers as `[{name, minutes}]`; a text of several lines becomes bullets; titles and timers need a Kinwall server newer than 1.0.2), and optionally `plan_date` + `plan_slot` (default `dinner`) + `plan_servings` to plan it, and `plan_calendar_id` (a Kinwall calendar ID; empty = none) to also put the planned meal on that calendar at the family's usual time for that meal, unless it already has an event. Returns `{recipeId, created, planned, mealId?, reason?, calendarEventId?, calendarError?}`: `planned: false` with a `reason` when that slot already has a meal; `calendarError` says why the meal got no event. |
| `kinwall.sync_events` | Keeps a set of events on a Kinwall calendar made in Kinwall (not a synced one): `calendar_id`, `source` (default `home_assistant`; names the set, e.g. `ha:hellofresh`), `events` (every event the source has now: `{external_id, title, start, end, all_day, notes, location}`; all-day events take dates with the end the day after the last day, timed ones date-times, in Home Assistant's time zone without an offset), and optionally `from` + `to` (dates). New events are added, changed ones updated, and ones of that source missing from the list removed; with `from`/`to`, only those starting in that window are removed, so past ones stay. Events made in Kinwall and events of other sources are never touched, and sending the same list again changes nothing. Returns `{created, updated, deleted}`. Needs a Kinwall server newer than 1.0.2. |
| `kinwall.night_screen` | Starts (`on: true`) or ends (`on: false`) the Night screen. `displays`: wall screens by their Night screen switch (or a paired display's name or Kinwall ID); leave it empty for every wall screen. `hours`: when "on" runs out on its own (default 12). Returns `{all, displays}`, the state of every wall screen. Needs a Kinwall server newer than 1.1.0. |
| `kinwall.plan_meal` | Plans a meal: `date`, `slot` (default `dinner`), and a `recipe_id` (such as `recipeId` from `import_recipe`) or a `title` for a free-form meal, plus optional `servings` and `notes`. Returns the meal. |

## Example automations

**Announce when all of a kid's chores are done**

```yaml
automation:
  - alias: "Announce when Avery's chores are done"
    trigger:
      - platform: state
        entity_id: sensor.avery_chores_remaining_today
        to: "0"
    condition:
      - condition: numeric_state
        entity_id: sensor.avery_points_today
        above: 0
    action:
      - service: tts.speak
        target:
          entity_id: tts.living_room
        data:
          message: "Avery finished all their chores today!"
```

**Flash the lights 10 minutes before an event**

```yaml
automation:
  - alias: "Flash lights before calendar events"
    trigger:
      - platform: calendar
        event: start
        entity_id: calendar.family
        offset: "-00:10:00"
    action:
      - service: light.turn_on
        target:
          entity_id: light.kitchen
        data:
          flash: short
```

**Add a chore when the dishwasher finishes**

```yaml
automation:
  - alias: "Unload dishwasher chore"
    trigger:
      - platform: state
        entity_id: sensor.dishwasher
        to: "Run finished"
    action:
      - service: todo.add_item
        target:
          entity_id: todo.anyone
        data:
          item: "Unload the dishwasher"
```

**Sensor-based reward**

```yaml
automation:
  - alias: "Unlock the tablet after 20 points"
    trigger:
      - platform: numeric_state
        entity_id: sensor.avery_points_today
        above: 19
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.avery_tablet_time
```

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements_test.txt
.venv/bin/python -m pytest tests/
```

## License

AGPL-3.0-or-later — see [LICENSE](LICENSE). Same license as Kinwall itself.

## Blueprints

### Kinwall reward moves a Nintendo Switch bedtime

When someone gets a chosen Kinwall reward (say "Nintendo Switch"), move a Switch's bedtime later for the rest of the day (6:30 PM by default), then put it back at midnight (to 6:00 PM by default). It only ever moves the bedtime later.

[![Import the blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/create-link/?redirect=blueprint_import&blueprint_url=https%3A%2F%2Fgithub.com%2FJohnDuprey%2Fkinwall-homeassistant%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fkinwall%2Freward_switch_bedtime.yaml)

1. Set up the **Nintendo Switch parental controls** integration and find the Switch's **Bedtime alarm** entity.
2. Create a **Toggle** helper, for example "Switch bedtime moved".
3. Import the blueprint and create an automation from it. Pick a long random **Webhook ID**, the reward name, the bedtime entity and the toggle.
4. In Kinwall, go to **Settings → Access → Webhooks → New webhook**. Use your Home Assistant webhook URL (`https://<your Home Assistant>/api/webhook/<Webhook ID>`, or your Home Assistant Cloud webhook URL) and choose the events `reward.redeemed` and `reward.approved`. Hosted Kinwall needs a URL reachable from the internet.

A reward that needs a parent's OK moves the bedtime once it's approved; one that doesn't moves it right away. Anyone who knows the webhook URL can trigger it, so keep the Webhook ID secret.

### Weekly meal kit import (HelloFresh)

Once a week (Sunday 10:00 by default), put your HelloFresh box on Kinwall's meal planner. Each meal you picked for the next delivery becomes a Kinwall recipe, with its ingredients scaled to your servings, its steps and a link to the recipe card, and is planned as a dinner: one a night from delivery day on, skipping nights that already have a dinner. Ingredients that ship in the box stay off your Kinwall grocery list; the pantry items you supply yourself (oil, salt, butter) go on it.

[![Import the blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/create-link/?redirect=blueprint_import&blueprint_url=https%3A%2F%2Fgithub.com%2FJohnDuprey%2Fkinwall-homeassistant%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fkinwall%2Fmeal_kit_import.yaml)

1. Set up the **HelloFresh** integration for Home Assistant, and this integration with an **admin** API key.
2. Import the blueprint and create an automation from it. The defaults import the **next delivery** with meals picked, at your plan's number of people, as dinners from delivery day; you can change the day and time, the servings, the first night (days after delivery), the meal (dinner, lunch…) and whether to skip weekends.
   **Add dinners to calendar** (empty by default: off) takes a Kinwall calendar ID. Each planned meal then also goes on that calendar, at your usual time for that meal (Kinwall Settings → Family → Meals) and as long as the recipe takes. Find the ID in Kinwall under **Settings → Calendars**: tap the calendar and it's at the bottom. A synced Google or Outlook calendar works too; the event shows up there as well. The event follows the meal if you move or change it in Kinwall. Needs the Kinwall server version that has meal calendar events.
3. To import now (for example after changing your picks), open the automation and choose **Run**.

Running it again updates the same recipes and finds the meals it already planned, even ones you moved to another night that week, so nothing is added twice. A meal that finds no free night in the seven it tries is imported to the recipe library without being planned. A meal you doubled is scaled for twice your servings. Needs Home Assistant 2025.4 or later.

Each HelloFresh step becomes a numbered step in Kinwall, with its short instructions as bullets you can tick off while cooking. Step photos, captions (as the step's title) and timers go along with the HelloFresh integration 3.03 or newer; in Kinwall's cooking mode a step's timers are its timer buttons, named ("Rice · 15 min"). Needs the Kinwall server version with recipe steps; an older server rejects the import, and step titles and timers need a Kinwall server newer than 1.0.2.

### Meal kit deliveries (HelloFresh)

Keeps your HelloFresh deliveries on a Kinwall calendar, checked every three hours and when Home Assistant starts. Each box that isn't skipped gets a **📦 HelloFresh delivery** event on its delivery day (the holiday-shifted day when HelloFresh moves it), in your delivery window when HelloFresh gives one ("Wednesdays: 8AM - 8PM" becomes 8 AM to 8 PM) and all day otherwise. Its notes list the meals you picked and, for example, "2 of 3 meals picked". A box that still needs meals picked also gets a **Pick HelloFresh meals** reminder at the selection deadline, in Home Assistant's time zone: a half-hour event ending at the deadline, or, when the deadline is before 6 AM, an all-day reminder the day before (notes say "by 2:59 AM Saturday").

[![Import the blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/create-link/?redirect=blueprint_import&blueprint_url=https%3A%2F%2Fgithub.com%2FJohnDuprey%2Fkinwall-homeassistant%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fkinwall%2Fmeal_kit_deliveries.yaml)

1. Set up the **HelloFresh** integration for Home Assistant, and this integration (1.5.0 or later) with an **admin** API key.
2. Make or pick a calendar in Kinwall for the deliveries (**Settings → Calendars**; it must be one made in Kinwall, not a synced Google or Outlook calendar) and copy its ID from the bottom of the calendar's settings.
3. Import the blueprint and create an automation from it with that **Kinwall calendar ID**. **Weeks ahead** (default 6) is how far ahead deliveries show; **Remind me to pick meals** (default on) adds the deadline reminders.

Each run replaces what it put on the calendar from today through the weeks ahead, so a skipped or cancelled delivery disappears and a changed window or pick updates its event. Past deliveries stay, and events you add yourself on that calendar are never changed. If HelloFresh returns no weeks (for example while it's signed out), the run stops without changing anything. Needs a Kinwall server newer than 1.0.2 and Home Assistant 2025.4 or later.

