# Kinwall for Home Assistant

Home Assistant integration and add-on for [Kinwall](https://github.com/JohnDuprey/kinwall), a
self-hosted, open-source family wall calendar + chore chart. The main Kinwall server lives in a
separate repo; this repo has:

- **`custom_components/kinwall`** — a HACS-installable integration: calendars, to-do lists, and
  sensors for each family member, kept live via a push webhook.
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
- **Poll interval** (integration Options, default 30s): how often the integration checks
  `GET /api/rev`. Real-time updates don't depend on this — the integration also registers a Kinwall
  webhook and refreshes immediately when the server pushes a change.

## Entities

One device per family member, plus a "Family" device for shared/aggregate entities.

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

AGPL-3.0-or-later — see [LICENSE](LICENSE). Same licence as Kinwall itself.
