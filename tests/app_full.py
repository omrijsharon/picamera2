"""Test shim.

This repository keeps the full application in `apps/app_full.py`.
Some upstream trees used a text reference here; make it valid Python so
`python -m compileall` succeeds.
"""

from apps.app_full import *  # noqa: F401,F403