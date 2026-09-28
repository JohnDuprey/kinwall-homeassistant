# Working on the Kinwall Home Assistant integration

The shared rules for all Kinwall repos are in [kinwall's AGENTS.md](https://github.com/JohnDuprey/kinwall/blob/main/AGENTS.md): test first,
Conventional Commits (checked in CI), docs with every change, the design and content rules. This
file adds what's specific to this repo: the `kinwall` custom integration and its blueprints.

## Checks

```bash
python -m pytest -q tests/           # CI also runs hassfest and the HACS check
```

## Rules

- Write the failing test in `tests/` first, for every service, sensor or config-flow change.
- Actions and services follow Home Assistant's conventions: `services.yaml` and `strings.json`
  describe every field, and errors are raised as `HomeAssistantError` with a plain message.
- A release bumps `version` in `custom_components/kinwall/manifest.json` (semver) with a
  `chore(release): x.y.z` commit. Say in the README which Kinwall server version a feature needs.
- Blueprints: every input has a name, a description and a safe default, and the blueprint's
  description says what it needs installed. Update the README's Blueprints section with them.
- Scopes for commits: `integration`, `blueprints`, `services`, `config-flow`, `docs`, `release`.
