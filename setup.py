#!/usr/bin/env python3

from setuptools import setup, find_packages

# Minimal packaging to allow `pip install -e .` for this contrib fork.
# This intentionally installs under the Python import namespace `picamera2_contrib`
# so it can coexist with the stock `picamera2` package.

setup(
    name="picamera2-contrib",
    version="0.0.0",
    description="Picamera2 contrib fork (side-by-side installable)",
    packages=find_packages(exclude=("tests*", "examples*", "apps*", "tools*")),
    python_requires=">=3.7",
)
