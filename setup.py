#!/usr/bin/env python3
"""
Setup script - installs MyCode as a CLI command.
Run: python setup.py install   (or)   pip install -e .
"""

from setuptools import setup, find_packages

setup(
    name="mycode",
    version="1.0.0",
    description="MyCode - Multi-Agent AI Coding Assistant (OpenCode-style clone)",
    long_description=(
        "An open-source OpenCode-style CLI tool with:\n"
        "  - Pre-built + custom LLM providers (Groq, Gemini, OpenRouter, DeepSeek, etc.)\n"
        "  - Normal chat mode\n"
        "  - Multi-agent mode (Planner -> Worker -> Bug Analyzer -> Fixer)\n"
        "  - Editable system prompts per agent\n"
        "  - File operation tools (read/write/edit/list/run)\n"
    ),
    long_description_content_type="text/plain",
    author="Custom Build",
    license="MIT",
    python_requires=">=3.9",
    packages=find_packages(),
    install_requires=[
        "openai>=1.50.0",
    ],
    entry_points={
        "console_scripts": [
            "mycode=mycode.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Code Generators",
    ],
)
