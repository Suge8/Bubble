"""
login_items.py

macOS login item toggle using user LaunchAgents.

Behavior:
- Darwin: creates/removes a LaunchAgent plist under
  ~/Library/LaunchAgents/com.bubble.launcher.plist and (boot)loads/unloads
  it using launchctl. ProgramArguments points to the app entry derived from
  bubble.launcher.get_executable().
- Non‑Darwin: operations are disabled; callers should disable the UI.

Notes:
- ServiceManagement.SMLoginItemSetEnabled requires a bundled helper with
  entitlements. For a Python app this is heavier, hence LaunchAgents is a
  practical, robust approach that doesn’t require extra permissions.
"""

from __future__ import annotations

import os
import platform
import pwd
import subprocess
from pathlib import Path
from typing import List, Tuple

import plistlib

# Internal label for the per-user LaunchAgent
AGENT_LABEL = "com.bubble.launcher"


def _is_darwin() -> bool:
    return platform.system().lower() == "darwin"


def _launch_agents_dir() -> Path:
    home = Path.home()
    return home / "Library" / "LaunchAgents"


def _plist_path() -> Path:
    return _launch_agents_dir() / f"{AGENT_LABEL}.plist"


def _program_args() -> List[str]:
    # Use the app’s own executable/program args abstraction
    try:
        from ..launcher import get_executable

        return list(get_executable())
    except Exception:
        # Minimal safe fallback to avoid crashing – won’t autostart
        return ["/usr/bin/true"]


def _write_plist(program_args: List[str]) -> None:
    plist = {
        "Label": AGENT_LABEL,
        "ProgramArguments": program_args,
        # Start at login
        "RunAtLoad": True,
        # Do not respawn on crash by default (leave to user)
        "KeepAlive": False,
        # Silence logs by default
        "StandardOutPath": "/dev/null",
        "StandardErrorPath": "/dev/null",
        # Background process for better behavior
        "ProcessType": "Background",
        # Environment: ensure PATH includes Homebrew for userland python if needed
        "EnvironmentVariables": {
            "PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        },
    }
    d = _launch_agents_dir()
    d.mkdir(parents=True, exist_ok=True)
    with _plist_path().open("wb") as f:
        plistlib.dump(plist, f)


def _uid() -> str:
    try:
        return str(os.getuid())
    except Exception:
        # Fallback via pwd
        return str(pwd.getpwnam(os.getlogin()).pw_uid)


def _launchctl(*args: str) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(["launchctl", *args], capture_output=True, text=True)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except FileNotFoundError:
        return 127, "", "launchctl not found"


def is_supported() -> bool:
    return _is_darwin()


def is_enabled() -> bool:
    if not _is_darwin():
        return False
    label = f"gui/{_uid()}/{AGENT_LABEL}"
    code, _, _ = _launchctl("print", label)
    if code == 0:
        return True
    # Fallback: consider enabled if plist exists
    return _plist_path().exists()


def set_enabled(enabled: bool) -> Tuple[bool, str]:
    """
    Enable/disable login item.

    Returns (ok, message)
    """
    if not _is_darwin():
        return False, "Login item is only available on macOS."

    plist_path = _plist_path()
    label_ref = f"gui/{_uid()}/{AGENT_LABEL}"

    if enabled:
        try:
            _write_plist(_program_args())
        except Exception as e:
            return False, f"Failed to write LaunchAgent: {e}"

        # Try modern bootstrapping first
        code, out, err = _launchctl("bootstrap", f"gui/{_uid()}", str(plist_path))
        if code != 0:
            # Fallback to legacy load
            code2, out2, err2 = _launchctl("load", "-w", str(plist_path))
            if code2 != 0:
                return False, f"launchctl failed: {err or err2 or out or out2}"
        # Ensure enabled
        _launchctl("enable", label_ref)
        return True, "Login item enabled"
    else:
        # Try modern bootout first
        _launchctl("disable", label_ref)
        code, out, err = _launchctl("bootout", label_ref)
        if code != 0:
            # Fallback to legacy unload
            _launchctl("unload", "-w", str(plist_path))
        try:
            if plist_path.exists():
                plist_path.unlink()
        except Exception:
            pass
        return True, "Login item disabled"
