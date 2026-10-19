# Changelog

The add-on version is the Kinwall server version it runs (`ghcr.io/johnduprey/kinwall:<version>`).

## 1.2.0

Runs Kinwall 1.2.0: connected to-do apps, family polls, outings, restaurant menus and orders,
German, and an easier-to-use calendar, Board and chore chart.

### Calendar and wall screens

- **Calendar has its own place** beside Home, with Day, Week, Month and Schedule views (3 Day on
  phones). Home holds Board and Newscast; find Board layouts and category filters under
  **Layout and filter** on its toolbar.
- Today's events put what's on now and next first. Meal events show whether dinner is cooked or
  ordered, and how many people have ordered. Events synced from two calendars appear once on
  the Board.
- Pick a default calendar and event length, and repeat an event yearly.
- Better layouts and text sizes on phones, tablets and wall screens, with a screen scale setting
  and a cast screen mode for smart displays.
- Picking someone on a shared wall remembers who's using it until it goes idle, so chores,
  votes and activities need fewer taps.

### Lists and shopping

- **Two-way to-do sync** with Todoist, Google Tasks and Microsoft To Do, including titles,
  completion, due dates, notes and checklist steps. Priority syncs where the app supports it.
  Connect under **Settings → Calendars → To-do apps**, then choose **Edit → Sync with…** on a
  to-do list. Changes in Kinwall go out within seconds; changes in the other app are checked
  about every two minutes. Parents see warnings and get notified if a sign-in stops working.
- **Get stuff done** walks through a checklist, including a chore's steps. Add its progress card
  to the Board or pin a checklist to a screen.
- Mark who an item is for. Shopping lists gain an add-item sheet, an on-sale flag, default stores
  for Groceries and Shopping, and easier aisle ordering.
- Shopping mode remembers where you found things, warns when a scanned item is already on the
  list, and offers Undo when you end a trip. Barcode matching and department grouping are fixed.

### Meals, polls and outings

- **Restaurants**: keep menus and family favorites together, import menus from links or photos,
  and collect everyone's order for pickup, delivery or eating out.
- **Family polls**: vote on plans, see the leading choice, pick a restaurant from the binder,
  and turn the result into a calendar event. Open polls appear on the Board.
- **Outings**: save things to do and places to go, mark interest, set reminders, and import ideas
  from links, flyers, maps and community calendars.
- Favorite recipes for each person. Cooking mode keeps instructions in view, and timers for
  ranges such as 15–20 minutes give a check chime before the final ring.

### Chores, rewards and family

- **Edit chores** and **Edit lists** replace press and hold on parent devices.
- Kids can suggest a chore for a parent to approve. Parents can give bonus points outside a
  chore, and chores can have a start time and timer.
- Activity chores count time while a kid is actually playing and show progress. Checklist chores
  finish when the last step is ticked, and points and leaderboards refresh correctly.
- Split a reward between several people and open a person's points history from their balance.
- Medicine refill cards help arrange a refill and track it with a to-do. Parents can see kids'
  due doses on their phone and correct a dose's recorded time or status.
- Turn a calendar event into a health visit, and log or correct reading for an earlier day.
- The library gains cover and shelf views, separate audiobook entries, richer book details,
  and more filters and sorting.
- Profile pictures can come from a photo, drawing or camera. Paint gains a pencil, more coloring
  pages, zoom and pan.

### Language and everyday improvements

- **German** across Kinwall's screens, reminders, notifications and other server-written text.
  Choose a family language and an optional language for each person. Thanks to
  [sudo-Foras666](https://github.com/sudo-Foras666) for the translation.
- Search across Settings, jump straight to help for the current page, and find advanced access
  settings together.
- Back closes the current sheet or full-screen mode. Unsaved forms ask before discarding changes.
  Larger touch targets, clearer errors with Try again, and better keyboard and landscape layouts.
- Security fixes strengthen sign-in refreshes, activity plugins, shared-content parsing and
  photo previews.

### Upgrading from 1.1.0

- Back up the Home Assistant app before updating, including its persistent data and encryption
  key. Database migrations run automatically at startup. Reload open Kinwall screens afterward;
  if a device keeps showing the old version, use **Settings → General → Troubleshooting →
  Clear cache and reload** in Kinwall.
- **Meal status change for API and MCP users:** `handled` is no longer accepted. Send `prepared`
  for Cooked or Ordered, or `planned`. Existing `handled` meals are converted automatically.
- Google Tasks and Microsoft To Do need the corresponding Google or Microsoft sign-in provider
  configured and a new tasks permission grant. The app's `public_url` is needed for those OAuth
  redirects. Todoist connects with an API token.
- Keep the separate **Kinwall HACS integration at 1.9.0 or later**, as with app 1.1.0. This app
  update runs the Kinwall server; the HACS integration is updated separately.

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
