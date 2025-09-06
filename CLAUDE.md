# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BubbleBot is a macOS AI overlay application that provides always-on-top access to multiple LLMs. It's built with Python and PyObjC frameworks, using native macOS frameworks like AppKit, Quartz, and WebKit.

## Development Commands

### Installation and Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Running the Application
```bash
python BubbleBot.py
# or
python -m src.bubblebot.main
```

### Testing
```bash
# Run all tests
python -m pytest

# Run specific test files
python test_app.py
python minimal_test.py
python simple_test.py
```

### Development Tools (optional)
```bash
# Code formatting
black src/

# Linting
flake8 src/
pylint src/

# Build macOS app bundle
python setup.py py2app
```

## Architecture

### Core Structure
- `src/bubblebot/` - Main application package
  - `main.py` - Entry point with argument parsing and signal handling
  - `app.py` - AppDelegate and main application class
  - `launcher.py` - Permissions and startup management
  - `health_checks.py` - Application health monitoring
  - `constants.py` - Application constants and configuration
  - `listener.py` - Global hotkey and event handling

### Component Architecture
- `components/` - Modular UI and functionality components
  - `platform_manager.py` - AI platform integration
  - `multiwindow_manager.py` - Multiple window management
  - `navigation_controller.py` - UI navigation
  - `homepage_manager.py` - Homepage UI management

### Models
- `models/` - Data models and configurations
  - `ai_window.py` - AI window model
  - `platform_config.py` - Platform configuration model

### Key Features
- Always-on-top overlay window
- Global hotkey support (default: ⌘+G)
- Multi-AI platform support (ChatGPT, Grok, Claude, etc.)
- Voice and text input
- Transparency control
- Meeting detection and auto-hide
- macOS native integration with PyObjC

### Permissions Required
- Microphone access for voice commands
- Accessibility access for global hotkeys

### Testing Strategy
The project includes various test files for different components:
- Unit tests in `tests/` directory
- Integration tests as standalone files (test_*.py)
- Debug utilities for development