# Repository Guidelines

## Project Structure & Module Organization
`app/` contains the Flask web app. Entry points live in `app/run.py` and `app/src/__init__.py`; HTTP handlers are split by blueprint in `app/src/routes/`, shared business logic lives in `app/src/services/`, and DB helpers live in `app/src/db.py`. Jinja templates are under `app/src/templates/`, static assets under `app/src/static/`, and uploaded files under `app/src/static/uploads/`. `db/init.sql` seeds MySQL. `scheduler/update_prices.py` updates stock prices on an interval. `nginx/` holds the reverse-proxy config used by Docker Compose.

## Build, Test, and Development Commands
Use Docker Compose from the repository root.

- `docker compose up --build`: build and start `web`, `app`, `db`, and `scheduler`.
- `docker compose down -v`: stop containers and reset the seeded MySQL volume.
- `docker compose restart app web scheduler`: reload application containers after code changes.
- `docker compose logs -f app`: follow Flask logs while debugging.
- `python app/run.py`: run the Flask app directly if you already have MySQL available.

## Coding Style & Naming Conventions
Follow the existing Python style: 4-space indentation, `snake_case` for functions and variables, and short module-level constants such as `DETAIL_HISTORY_LIMIT`. Keep route handlers thin and move reusable logic into `app/src/services/` or `app/src/utils/`. Template filenames and static asset names should stay lowercase and descriptive, for example `templates/stocks/detail.html` or `static/js/app.js`. No formatter or linter is configured in-repo, so keep edits consistent with surrounding code.

## Testing Guidelines
There is no automated test suite checked in yet. For changes, verify flows manually with `docker compose up --build` and exercise the main routes: `/auth/login`, `/stocks`, `/wallet/transfer`, `/community`, and `/admin`. When adding tests, place them under a new `tests/` package and prefer `pytest` with names like `test_auth_login.py`.

## Commit & Pull Request Guidelines
Git history is minimal; the existing commit uses a short imperative subject (`Initial vulnerable finance platform`). Keep commits focused and written in the imperative mood, for example `Add portfolio snapshot endpoint`. PRs should include a brief behavior summary, impacted routes or schema changes, manual verification steps, and screenshots for template or CSS changes.

## Security & Configuration Notes
This repository is intentionally vulnerable for training purposes. Do not remove or “fix” security weaknesses unless the task explicitly asks for it. Keep secrets in `.env.example`-style environment variables, and treat `db/init.sql` and `app/src/static/uploads/` as development data, not production-safe assets.
