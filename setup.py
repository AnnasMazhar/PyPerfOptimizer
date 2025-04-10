from setuptools import setup, find_packages
import os

# Read the long description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pyperfoptimizer",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive Python package for unified performance profiling, visualization, and optimization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pyperfoptimizer",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/pyperfoptimizer/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Debuggers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=find_packages("src"),
    package_dir={"": "src"},
    python_requires=">=3.7",
    install_requires=[
        "astor",
        "line-profiler",
        "memory-profiler",
        "matplotlib",
        "plotly",
        "flask",
    ],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "pyperfoptimizer=pyperfoptimizer.cli:main",
        ],
    },
)