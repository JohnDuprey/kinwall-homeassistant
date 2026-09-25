# Kinwall Add-on

Self-hosted family wall calendar + chore chart, running as a Home Assistant add-on.

## Install

1. Home Assistant → Settings → Add-ons → Add-on Store → ⋮ → Repositories → add
   `https://github.com/JohnDuprey/kinwall-homeassistant`.
2. Find "Kinwall" in the store and install it.
3. Configure the options below, then start the add-on.
4. Open it from the sidebar (ingress), or via the optional direct LAN port for kiosk use.

## Options

| Option | Description |
|---|---|
| `google_client_id` / `google_client_secret` | Google OAuth app credentials, for two-way Google Calendar sync. Optional. |
| `microsoft_client_id` / `microsoft_client_secret` | Microsoft/Graph OAuth app credentials, for two-way Outlook sync. Optional. |
| `public_url` | The URL Kinwall is reachable at (used for OAuth redirects). Required if you use Google or Microsoft sync. |
| `timezone` | Household timezone, e.g. `America/New_York`. Defaults to the HA host's timezone if unset. |

## Home Assistant integration

The add-on runs Kinwall with `ALLOW_PRIVATE_WEBHOOK_URLS=1`, so the Kinwall integration's push webhook (registered at Home Assistant's internal URL) works out of the box; no options needed. The add-on's version is the Kinwall server version it runs (`ghcr.io/johnduprey/kinwall:<version>`).

## iPad kiosk setup

The wall display should talk to Kinwall directly over the LAN, not through ingress (ingress requires
an authenticated HA session and isn't meant for an always-on kiosk browser):

1. In the add-on's **Network** tab, map port `8080` to a fixed host port (e.g. `8080`) so the iPad can
   reach `http://<home-assistant-ip>:8080` directly.
2. In Kinwall Settings → API keys, create a **display**-scope key (read/write to calendar & chores,
   no access to accounts, keys, or webhooks).
3. On the iPad, open Safari to `http://<home-assistant-ip>:8080/?key=<display-key>` once — it stores
   the key in `localStorage` and strips it from the URL.
4. Share → Add to Home Screen, then open the app icon for full-screen kiosk mode.

## Security notes

- Ingress access is gated by your Home Assistant login — anyone who can reach your HA UI can reach
  Kinwall through ingress.
- The optional direct LAN port (8080) is **not** authenticated by Home Assistant; only enable it on a
  trusted network, and use a display-scope key (not an admin key) for the kiosk.
- The database encryption key is generated on first run and persisted at `/data/encryption.key`
  (0600). Back up `/data` if you want to preserve OAuth tokens, webhooks, and encrypted account
  credentials across reinstalls.

## Requirements this add-on places on the main Kinwall image

This add-on maps Home Assistant's `/data/options.json` to the main app's expected environment
variables and does not implement Kinwall itself — the main `ghcr.io/johnduprey/kinwall` image needs
an entrypoint that:

- Reads `/data/options.json` (when present) and maps its keys to the env vars in `SPEC.md`
  (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `MS_CLIENT_ID`, `MS_CLIENT_SECRET`, `PUBLIC_URL`, plus a
  `timezone` value used as `TZ`/default household timezone).
- Sets `DATA_DIR=/data` so the sqlite file and generated `encryption.key` land on the add-on's
  persistent `/data` volume (this add-on's `map: [{type: data}]`).
- Serves correctly behind Home Assistant ingress: honors the `X-Ingress-Path` header (or serves all
  assets with relative paths / a runtime-configurable `<base href>`) so `web/dist` doesn't hardcode
  absolute root-relative URLs that break under a path prefix.
