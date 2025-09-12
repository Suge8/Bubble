"""Launcher for both dev (source tree) and bundled app.

Tries to import from installed/bundled package first, then falls back to
adding ./src to sys.path for developer runs.
"""

import os
import sys

try:
    # When installed or bundled by py2app
    from bubble.main import main  # type: ignore
except ModuleNotFoundError:
    # Development fallback: add ./src to path
    here = os.path.dirname(__file__)
    src_path = os.path.join(here, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    from bubble.main import main  # type: ignore


if __name__ == "__main__":
    main()

