# Changelog

The add-on version is the Kinwall server version it runs (`ghcr.io/johnduprey/kinwall:<version>`).

## 1.0.2

- Fixed: the add-on could not start because `/data` is mounted root-owned and the server runs as an unprivileged user (`EACCES` on `/data/encryption.key`). The container now makes `/data` writable, then drops privileges.

## 1.0.1

- Fixed: the Kinwall integration's push webhook was refused (Home Assistant's internal URL is a LAN address). The add-on now runs with `ALLOW_PRIVATE_WEBHOOK_URLS=1`, so push updates work out of the box.
- Fixed: the `microsoft_client_id` / `microsoft_client_secret` options never reached the server.

## 1.0.0

- First release: Kinwall server as a Home Assistant add-on with ingress, optional direct LAN port for a kiosk iPad, and Google / Microsoft OAuth options.
