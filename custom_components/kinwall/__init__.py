"""The Kinwall integration."""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import logging
import secrets
from urllib.parse import urlparse

from aiohttp.web import Request, Response
from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_URL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.network import get_url

from .api import KinwallApiError, KinwallClient
from .const import (
    ALL_WEBHOOK_EVENTS,
    CONF_KINWALL_WEBHOOK_ID,
    CONF_KINWALL_WEBHOOK_SECRET,
    CONF_WEBHOOK_ID,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    EVENT_PREFIX,
    OPT_POLL_INTERVAL,
    SIGNATURE_HEADER,
)
from .coordinator import KinwallCoordinator
from .entity import FAMILY_DEVICE_KEY

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CALENDAR, Platform.TODO, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    client = KinwallClient(session, entry.data[CONF_URL], entry.data[CONF_API_KEY])
    poll_interval = entry.options.get(OPT_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
    coordinator = KinwallCoordinator(hass, client, poll_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Create the "Family" device up front so member devices (set up by the entity platforms
    # below, in undefined order) can hang off it by id.
    family_device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"{entry.entry_id}_{FAMILY_DEVICE_KEY}")},
        name="Family",
        manufacturer="Kinwall",
    )
    coordinator.family_device_id = family_device.id

    await _async_register_webhook(hass, entry, client)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await _async_unregister_webhook(hass, entry)
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


def _is_private_host(url: str) -> bool:
    """True for localhost, .local/.internal names and RFC1918/link-local/CGNAT addresses."""
    host = (urlparse(url).hostname or "").lower().rstrip(".")
    if host == "localhost" or host.endswith((".local", ".internal", ".localhost", ".lan", ".home")):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_private or ip in ipaddress.ip_network("100.64.0.0/10")  # CGNAT / Tailscale


async def _async_register_webhook(hass: HomeAssistant, entry: ConfigEntry, client: KinwallClient) -> None:
    """Register an HA webhook and point a new Kinwall webhook at it."""
    webhook_id = entry.data.get(CONF_WEBHOOK_ID)
    kinwall_webhook_id = entry.data.get(CONF_KINWALL_WEBHOOK_ID)
    secret = entry.data.get(CONF_KINWALL_WEBHOOK_SECRET)

    new_data = dict(entry.data)
    if not webhook_id:
        webhook_id = webhook.async_generate_id()
        new_data[CONF_WEBHOOK_ID] = webhook_id

    remote = not _is_private_host(entry.data[CONF_URL])
    try:
        # A Kinwall on the LAN (the add-on, a NAS) can reach HA's internal URL. A hosted or
        # otherwise remote Kinwall can only reach a public one, so that case insists on HA's
        # external URL (Settings → System → Network) rather than silently falling back to a LAN
        # address the server would refuse.
        if remote:
            base_url = get_url(hass, allow_internal=False, allow_ip=False, prefer_external=True)
        else:
            base_url = get_url(hass, prefer_external=False, allow_internal=True)
        ir.async_delete_issue(hass, DOMAIN, f"external_url_{entry.entry_id}")
    except Exception:  # noqa: BLE001 - NoURLAvailableError: nothing configured/derivable
        if remote:
            _LOGGER.warning(
                "Kinwall at %s is not on your network, so it needs Home Assistant's external URL to push updates; "
                "set it under Settings → System → Network. Falling back to polling.", entry.data[CONF_URL],
            )
            ir.async_create_issue(
                hass, DOMAIN, f"external_url_{entry.entry_id}", is_fixable=False, severity=ir.IssueSeverity.WARNING,
                translation_key="external_url_required", translation_placeholders={"url": entry.data[CONF_URL]},
            )
        else:
            _LOGGER.warning("Kinwall: no HA base URL available; skipping push webhook registration")
        webhook.async_register(hass, DOMAIN, "Kinwall", webhook_id, _handle_webhook)
        if new_data != entry.data:
            hass.config_entries.async_update_entry(entry, data=new_data)
        return

    callback_url = f"{base_url}{webhook.async_generate_path(webhook_id)}"

    if not kinwall_webhook_id or not secret:
        secret = secrets.token_hex(32)
        try:
            created = await client.create_webhook(callback_url, secret, ALL_WEBHOOK_EVENTS)
            kinwall_webhook_id = created["id"]
        except KinwallApiError as err:
            _LOGGER.warning("Kinwall: failed to register server-side webhook at %s: %s", callback_url, err)
            kinwall_webhook_id = None
        new_data[CONF_KINWALL_WEBHOOK_ID] = kinwall_webhook_id
        new_data[CONF_KINWALL_WEBHOOK_SECRET] = secret

    if new_data != entry.data:
        hass.config_entries.async_update_entry(entry, data=new_data)

    webhook.async_register(hass, DOMAIN, "Kinwall", webhook_id, _handle_webhook)


async def _async_unregister_webhook(hass: HomeAssistant, entry: ConfigEntry) -> None:
    webhook_id = entry.data.get(CONF_WEBHOOK_ID)
    if webhook_id:
        webhook.async_unregister(hass, webhook_id)

    kinwall_webhook_id = entry.data.get(CONF_KINWALL_WEBHOOK_ID)
    if kinwall_webhook_id:
        session = async_get_clientsession(hass)
        client = KinwallClient(session, entry.data[CONF_URL], entry.data[CONF_API_KEY])
        try:
            await client.delete_webhook(kinwall_webhook_id)
        except Exception as err:  # noqa: BLE001 - best effort cleanup
            _LOGGER.debug("Kinwall: could not delete server-side webhook: %s", err)


async def _handle_webhook(hass: HomeAssistant, webhook_id: str, request: Request) -> Response:
    """Verify HMAC, fire an HA bus event, and trigger a coordinator refresh."""
    body = await request.read()

    entry = next(
        (e for e in hass.config_entries.async_entries(DOMAIN) if e.data.get(CONF_WEBHOOK_ID) == webhook_id),
        None,
    )
    if entry is None:
        return Response(status=404)

    secret = entry.data.get(CONF_KINWALL_WEBHOOK_SECRET)
    signature = request.headers.get(SIGNATURE_HEADER, "")
    if secret:
        expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            _LOGGER.warning("Kinwall: rejected webhook with invalid signature")
            return Response(status=401)

    try:
        payload = json.loads(body)
    except ValueError:
        return Response(status=400)

    event_type = payload.get("type", "unknown")
    hass.bus.async_fire(f"{EVENT_PREFIX}{event_type.replace('.', '_')}", payload.get("data", {}))

    coordinator: KinwallCoordinator | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is not None:
        await coordinator.async_request_full_refresh()

    return Response(status=200)
