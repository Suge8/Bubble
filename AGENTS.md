# Repository Guidelines

## Project Structure & Module Organization
- `src/bubblebot/`: Core app (GUI, hotkey, managers). Key modules: `main.py`, `app.py`, `listener.py`, `components/`, `models/`, `logo/` assets.
- `tests/`: Pytest suite (configured via `pyproject.toml`).
- Entry points: `BubbleBot.py` (dev runner) and console script `bubblebot` (after install).

## Build, Test, and Development Commands
- Setup env: `python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`.
- Run locally (dev): `python BubbleBot.py` or `python -m bubblebot.main`.
- Permissions check: `python -m bubblebot.main --check-permissions`.
- Tests: `pytest` (uses `tests/`), verbose: `pytest -v --tb=short`.
- Format: `black src tests`.
- Lint: `flake8 src tests` and `pylint src/bubblebot`.
- macOS app bundle (Darwin): `python setup.py py2app`.

## Coding Style & Naming Conventions
- Python 3.10+. Black enforced (`line-length = 88`). Use 4‑space indentation.
- Naming: modules/functions `snake_case`, classes `CamelCase`, constants `UPPER_SNAKE`.
- Keep UI/event code small and composable; prefer pure helpers for logic under `src/bubblebot/`.

## Testing Guidelines
- Framework: Pytest. Configured patterns: files `test_*.py`, classes `Test*`, functions `test_*`.
- Place tests in `tests/`. Run selectively with `pytest -k <expr>`.
- If adding macOS‑specific tests, guard or skip when not on Darwin to keep CI green.

## Architecture Overview
- HomepageManager: manages first‑launch flow, enabled platforms, and default AI. Persists user config at `~/Library/Application Support/BubbleBot/config.json` and renders simple HTML for the WebView (first‑run guide and platform management).
- NavigationController: central page state machine (`homepage` ↔ `chat`) with history/back handling. Exposes a JS bridge for WebView actions and notifies `AppDelegate` to update title, back button, and AI selector.
- MultiWindowManager: creates and tracks up to 5 concurrent NSWindow/WebView instances across platforms. Coordinates with models in `models/` and `PlatformConfig`, handles geometry/activation, and provides `createWindowForPlatform_` / `closeWindow_` helpers.

## Commit & Pull Request Guidelines
- History shows no strict convention; use Conventional Commits (e.g., `feat:`, `fix:`, `docs:`) with a clear scope.
- PRs must include: concise description, linked issues, steps to verify, and screenshots/GIFs for UI changes.
- Require green checks: `pytest`, `black`, `flake8`, and `pylint` on touched code.

## Security & Configuration Tips
- Permissions: app needs macOS Accessibility (hotkeys) and Microphone (voice). Test `--check-permissions` before shipping changes.
- Config lives at `~/Library/Application Support/BubbleBot/config.json`. Do not commit user configs or secrets.
- Packaging: build on macOS only; verify icons in `src/bubblebot/logo/` are included.
