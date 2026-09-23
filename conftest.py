"""Pytest configuration to prioritize the local repository over global installations.

Change facilitated by Antigravity using model Gemini 3.1 Pro (Low).
"""

import os
import sys

_repo_root = os.path.dirname(__file__)

# Force the local repository root to be at the front of sys.path
if _repo_root in sys.path:
    sys.path.remove(_repo_root)
sys.path.insert(0, _repo_root)

# If pytest already imported 'mezcla' from a globally installed package
# (due to plugins or other initialization), remove it so the local one is used.
if "mezcla" in sys.modules:
    if not sys.modules["mezcla"].__file__.startswith(_repo_root):
        # Remove the main module
        del sys.modules["mezcla"]
        # Remove all loaded submodules
        for _k in list(sys.modules.keys()):
            if _k.startswith("mezcla."):
                del sys.modules[_k]
