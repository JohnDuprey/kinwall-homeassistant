# Changelog

The add-on version is the Kinwall server version it runs (`ghcr.io/johnduprey/kinwall:<version>`).

## 1.1.0

- Runs Kinwall 1.1.0: the Board, meals and recipes, groceries in store order, rewards, medicines, check-ins, Newscast, a family library, Peacock as the default look and a new logo, plus many fixes. See the [release notes](https://github.com/JohnDuprey/kinwall/releases/tag/v1.1.0), and read their Upgrading section first.
- Passkeys work at the address Home Assistant serves the app on (`public_url` is only needed for Google or Microsoft sign-in).
- New app icon and logo.
- Pair it with the Kinwall integration 1.9.0 or later.

## 1.0.3

- Fixed: adding a passkey failed with "Unexpected registration response origin" when Home Assistant serves https itself (for example on port 8443). Kinwall now accepts the https address of the host the request came in on.

## 1.0.2

- Fixed: the add-on could not start because `/data` is mounted root-owned and the server runs as an unprivileged user (`EACCES` on `/data/encryption.key`). The container now makes `/data` writable, then drops privileges.

## 1.0.1

- Fixed: the Kinwall integration's push webhook was refused (Home Assistant's internal URL is a LAN address). The add-on now runs with `ALLOW_PRIVATE_WEBHOOK_URLS=1`, so push updates work out of the box.
- Fixed: the `microsoft_client_id` / `microsoft_client_secret` options never reached the server.

## 1.0.0

- First release: Kinwall server as a Home Assistant add-on with ingress, optional direct LAN port for a kiosk iPad, and Google / Microsoft OAuth options.
