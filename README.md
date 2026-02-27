# caas_schedule_script

## Environment setup

Create a `.env` file (or copy from `.env.example`) and set these values:

- `CAAS_EMAIL`
- `CAAS_PASSWORD`
- `MATTERMOST_WEBHOOK_URL`
- `CAAS_BASE_URL` (optional)

## Auto-accept schedule (PKT)

Auto-accept time windows are configurable in `.env`:

- `AUTO_ACCEPT_ENABLED_DAYS` (comma-separated weekday names)
- `AUTO_ACCEPT_EXTENDED_DAYS` (comma-separated weekday names)
- `AUTO_ACCEPT_EXTENDED_START` / `AUTO_ACCEPT_EXTENDED_END`
- `AUTO_ACCEPT_DEFAULT_START` / `AUTO_ACCEPT_DEFAULT_END`

Default configuration:

- Thursday and Friday: `06:00` to `22:00`
- All other enabled days: `07:00` to `17:00`