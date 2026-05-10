# Contributing to PyPerfOptimizer

## Development Setup

```bash
git clone https://github.com/AnnasMazhar/PyPerfOptimizer.git
cd PyPerfOptimizer
pip install -e .
pip install pytest ruff libcst
```

## Running Tests

```bash
python -m pytest tests/ -v    # 135 tests
ruff check src/ tests/        # lint
```

## Adding a New Pattern

1. Create `src/pyperfoptimizer/autofix/patterns/your_pattern.py`
2. Implement `detect()` and optionally `transform()` using libcst
3. Register in `src/pyperfoptimizer/autofix/patterns/__init__.py`
4. Add tests in `tests/test_autofix/`
5. Verify: `python -m pytest tests/ -v`

## Submitting Changes

1. Fork and create a branch
2. Make your changes
3. Run tests and lint
4. Submit a pull request with clear description

## Reporting Issues

Include: Python version, OS, steps to reproduce, expected vs actual behavior.
