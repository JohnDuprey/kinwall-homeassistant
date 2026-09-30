"""Constants for the Kinwall integration."""
from datetime import timedelta

DOMAIN = "kinwall"

CONF_API_KEY = "api_key"
CONF_WEBHOOK_ID = "webhook_id"
CONF_KINWALL_WEBHOOK_ID = "kinwall_webhook_id"
CONF_KINWALL_WEBHOOK_SECRET = "kinwall_webhook_secret"
CONF_KINWALL_WEBHOOK_URL = "kinwall_webhook_url"  # the callback we registered; re-registered when HA's URL changes
CONF_KINWALL_WEBHOOK_EVENTS = "kinwall_webhook_events"  # the events it was registered with; re-registered when ALL_WEBHOOK_EVENTS changes

DEFAULT_POLL_INTERVAL = 30  # seconds
OPT_POLL_INTERVAL = "poll_interval"
OPT_CHORE_POINTS = "chore_points"  # points for chores created from HA (todo.add_item / automations)
DEFAULT_CHORE_POINTS = 5

MIN_POLL_INTERVAL = 10
MAX_POLL_INTERVAL = 3600

DEFAULT_SCAN_INTERVAL = timedelta(seconds=DEFAULT_POLL_INTERVAL)

EVENTS_WINDOW_PAST_DAYS = 1
EVENTS_WINDOW_FUTURE_DAYS = 60

SIGNATURE_HEADER = "X-Kinwall-Signature"

# Webhook -> HA bus event name prefix. Kinwall bus event "chore.completed" becomes
# "kinwall_chore_completed".
EVENT_PREFIX = "kinwall_"

# The server's bus events (server/src/bus.ts BusEventType) HA subscribes to. Each one fires
# kinwall_<type> on HA's bus once its signature checks out. Changing this list re-registers the
# Kinwall webhook on the next setup.
ALL_WEBHOOK_EVENTS = [
    "member.changed",
    "calendar.changed",
    "calendar.synced",
    "events.changed",
    "chore.changed",
    "chore.completed",
    "chore.uncompleted",
    "list.changed",
    "list.item.changed",
    "settings.changed",
    "display.night_screen",
    "reward.redeemed",  # the Switch bedtime blueprint
    "reward.approved",
    "reward.given",
]
