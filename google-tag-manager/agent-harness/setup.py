#!/usr/bin/env python3
"""setup.py for cli-anything-google-tag-manager

Install with: pip install -e .
"""
from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-google-tag-manager",
    version="1.0.0",
    author="cli-anything contributors",
    author_email="",
    description=(
        "CLI harness for Google Tag Manager API v2 — manage accounts, containers, "
        "workspaces, tags, triggers, variables, folders, environments, and permissions."
    ),
    long_description=(
        "Agent-native CLI for Google Tag Manager. Provides full access to GTM API v2 "
        "resources via a structured command-line interface with REPL, JSON output, and "
        "environment-variable-based context management."
    ),
    long_description_content_type="text/markdown",
    url="https://github.com/HKUDS/CLI-Anything",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    package_data={
        "cli_anything.google_tag_manager": ["skills/*.md"],
    },
    include_package_data=True,
    install_requires=[
        "click>=8.0.0",
        "prompt-toolkit>=3.0.0",
        "google-api-python-client>=2.0.0",
        "google-auth>=2.0.0",
        "google-auth-oauthlib>=1.0.0",
        "google-auth-httplib2>=0.1.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cli-anything-google-tag-manager=cli_anything.google_tag_manager.google_tag_manager_cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    zip_safe=False,
)
