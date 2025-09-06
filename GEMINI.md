# BubbleBot Project Overview

This document provides a comprehensive overview of the BubbleBot project, including its purpose, architecture, and development guidelines.

## 1. Project Purpose

BubbleBot is a local-first, always-on-top AI overlay for macOS that provides seamless, private access to various LLMs like ChatGPT, Grok, Perplexity, Claude, and Gemini. It is designed to be a lightweight, distraction-free tool that is always available when you need it.

## 2. Architecture

The project is a Python application built using the following technologies:

*   **Python 3.10+**: The core language for the application.
*   **PyObjC**: For interacting with macOS native APIs, including AppKit, Quartz, and WebKit.
*   **SpeechRecognition**: For voice command input.

The application is structured as follows:

*   `src/bubblebot/`: The main source code for the application.
    *   `main.py`: The entry point of the application.
    *   `app.py`: The core application logic, including window management and event handling.
    *   `components/`: Various components of the application, such as the homepage manager, multi-window manager, and navigation controller.
    *   `models/`: Data models for the application, such as the AI window and platform configuration.
*   `tests/`: Unit and integration tests for the application.
*   `setup.py`: The setup script for the application, used for packaging and distribution.
*   `requirements.txt`: A list of Python dependencies for the project.

## 3. Building and Running

### 3.1. Running the Application

To run the application, follow these steps:

```bash
git clone https://github.com/N-Saipraveen/bubblebot-mac.git
cd bubblebot-mac

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

python BubbleBot.py
```

### 3.2. Building a Distributable Application

To build a distributable application package, run the following command:

```bash
python setup.py py2app
```

This will create a `BubbleBot.app` file in the `dist/` directory.

## 4. Development Conventions

### 4.1. Code Style

The project follows the standard PEP 8 style guide for Python code. Please ensure that your code adheres to these guidelines.

### 4.2. Testing

The project uses `pytest` for testing. To run the tests, use the following command:

```bash
pytest
```

### 4.3. Contributions

Contributions are welcome! Please follow these steps to contribute:

1.  Fork the repository.
2.  Create a feature branch.
3.  Submit a pull request.
