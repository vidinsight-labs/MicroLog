"""
Setup script for MicroLog package.

This file is provided for compatibility with older build tools.
Modern builds should use pyproject.toml instead.
"""

from setuptools import setup

# Read README for long description
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "Modern Python logging library with distributed tracing support"

setup(
    name="microlog",
    version="0.1.0",
    author="MicroLog Team",
    author_email="team@microlog.dev",
    description="Modern Python logging library with distributed tracing support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/microlog",
    package_dir={"": "src"},
    packages=["microlog"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ],
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

