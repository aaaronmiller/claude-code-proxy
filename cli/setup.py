#!/usr/bin/env python3
"""
Setup script for Claude Proxy CLI

Usage:
    pip install .
    claude-proxy --help
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="claude-proxy-cli",
    version="1.0.0",
    author="Claude Proxy Team",
    author_email="claude-proxy@example.com",
    description="Command-line interface for Claude Proxy analytics platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/claude-proxy/claude-proxy",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "claude-proxy=claude_proxy:main",
        ],
    },
    project_urls={
        "Documentation": "https://claude-proxy.readthedocs.io/",
        "Source": "https://github.com/claude-proxy/claude-proxy",
        "Tracker": "https://github.com/claude-proxy/claude-proxy/issues",
    },
)
