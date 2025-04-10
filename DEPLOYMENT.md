# Deployment Guide for PyPerfOptimizer

This guide explains how to deploy PyPerfOptimizer to GitHub and PyPI.

## Deploying to GitHub

1. Create a GitHub repository:
   - Go to [GitHub](https://github.com) and sign in
   - Click on the "+" icon in the upper right corner
   - Select "New repository"
   - Name the repository "pyperfoptimizer"
   - Add a description
   - Choose public or private
   - Click "Create repository"

2. Push your local code to GitHub:
   ```bash
   # Initialize Git repository (if not already done)
   git init
   
   # Add all files
   git add .
   
   # Commit the changes
   git commit -m "Initial commit"
   
   # Add the remote repository
   git remote add origin https://github.com/yourusername/pyperfoptimizer.git
   
   # Push to GitHub
   git push -u origin main
   ```

3. Enable GitHub Pages:
   - Go to your repository settings
   - Scroll down to the "GitHub Pages" section
   - Select the "main" branch and "/docs" folder
   - Click "Save"
   - Visit your new site at `https://yourusername.github.io/pyperfoptimizer/`

## Deploying to PyPI

### Setting up PyPI

1. Register on PyPI:
   - Go to [PyPI](https://pypi.org/account/register/)
   - Create an account if you don't have one

2. Create an API token:
   - Go to your account settings
   - Click on "API tokens"
   - Create a new token with the scope "Entire account"
   - Copy and save this token securely

3. Add the token to GitHub secrets:
   - Go to your GitHub repository
   - Click on "Settings"
   - Click on "Secrets and variables" -> "Actions"
   - Click "New repository secret"
   - Name: `PYPI_API_TOKEN`
   - Value: paste your PyPI token
   - Click "Add secret"

### Manual Deployment to PyPI

1. Build the distribution package:
   ```bash
   # Run the publish script
   ./publish.sh
   ```

2. Upload to PyPI:
   ```bash
   # For production PyPI
   twine upload dist/*
   
   # For TestPyPI (testing)
   twine upload --repository-url https://test.pypi.org/legacy/ dist/*
   ```

### Automatic Deployment using GitHub Actions

1. Create a new release on GitHub:
   - Go to your repository
   - Click on "Releases"
   - Click "Create a new release"
   - Tag version: `v0.1.0` (must match the version in setup.py)
   - Release title: "PyPerfOptimizer 0.1.0"
   - Description: Add release notes
   - Click "Publish release"

2. GitHub Actions will automatically:
   - Run tests
   - Build the package
   - Upload to PyPI

## Updating the Package

1. Update the version in `src/pyperfoptimizer/__init__.py` and `setup.py`
2. Commit your changes
3. Create a new tag and release on GitHub
4. GitHub Actions will automatically deploy the new version

## Testing the Deployment

After deploying to PyPI, you can test the installation:

```bash
# Create a new virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install the package
pip install pyperfoptimizer

# Test importing
python -c "import pyperfoptimizer; print(pyperfoptimizer.__version__)"
```