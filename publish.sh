#!/bin/bash

# Clean up any previous builds
rm -rf dist build *.egg-info

# Ensure required packages are installed
pip install --upgrade pip
pip install --upgrade build twine setuptools wheel

# Build the package
python -m build

# Check the built package
twine check dist/*

echo "Package built successfully!"
echo "To upload to PyPI, run:"
echo "twine upload dist/*"
echo ""
echo "To upload to TestPyPI, run:"
echo "twine upload --repository-url https://test.pypi.org/legacy/ dist/*"