# GitHub Actions CI/CD Workflows

This directory contains GitHub Actions workflows for automated testing and code quality checks for the Dataiku IaC project.

## Workflows

### 1. Tests (`test.yml`)

**Trigger:**
- Push to `master` or `main` branches
- All pull requests

**What it does:**
- Runs on Python 3.8, 3.9, 3.10, and 3.11 (matrix strategy)
- Executes comprehensive test suite (278+ tests):
  - Unit tests (`tests/iac/unit/`)
  - Integration tests (`tests/iac/integration/`)
  - Scenario tests (`tests/iac/scenarios/`)
  - Remaining IaC tests
- Generates coverage reports (XML, HTML, and terminal output)
- **Enforces 85% minimum coverage threshold** (build fails if below)
- Uploads coverage to Codecov (Python 3.10 only)
- Archives coverage reports as artifacts (7-day retention)
- Provides test summary in GitHub Actions UI

**Key Features:**
- Parallel testing across Python versions (fail-fast: false)
- Incremental coverage tracking with `--cov-append`
- Detailed failure output with `--tb=short`
- Pip caching for faster builds
- Coverage artifacts for debugging

**Coverage Threshold:**
```bash
coverage report --fail-under=85
```

### 2. Lint (`lint.yml`)

**Trigger:**
- Push to `master` or `main` branches
- All pull requests

**What it does:**
- Runs on Python 3.10 (single version, fast checks)
- Code quality tools:
  - **Ruff** - Fast Python linter (replaces Flake8, isort, etc.)
  - **Black** - Code formatter verification
  - **MyPy** - Type checking (continue-on-error: true)

**Key Features:**
- Ruff output formatted for GitHub annotations
- Black runs in check mode (doesn't modify files)
- MyPy runs with relaxed settings (informational)
- Fast execution (~30 seconds typical)

**Tool Configuration:**

```bash
# Ruff (linting)
ruff check dataikuapi/iac/ --output-format=github

# Black (formatting check)
black --check dataikuapi/iac/

# MyPy (type checking - informational)
mypy dataikuapi/iac/ --ignore-missing-imports --no-strict-optional
```

## Workflow Status

| Workflow | Status Badge |
|----------|--------------|
| Tests | [![Tests](https://github.com/dataiku/dataiku-api-client-python/actions/workflows/test.yml/badge.svg)](https://github.com/dataiku/dataiku-api-client-python/actions/workflows/test.yml) |
| Lint | [![Lint](https://github.com/dataiku/dataiku-api-client-python/actions/workflows/lint.yml/badge.svg)](https://github.com/dataiku/dataiku-api-client-python/actions/workflows/lint.yml) |

## Local Development

### Running Tests Locally

```bash
# Install test dependencies
pip install -e .
pip install pytest pytest-cov pytest-xdist pytest-mock pyyaml

# Run all tests with coverage
pytest tests/iac/ --cov=dataikuapi.iac --cov-report=term-missing

# Run specific test categories
pytest tests/iac/unit/         # Unit tests only
pytest tests/iac/integration/  # Integration tests only
pytest tests/iac/scenarios/    # Scenario tests only

# Check coverage threshold
coverage report --fail-under=85
```

### Running Linters Locally

```bash
# Install linting tools
pip install ruff black mypy types-requests types-python-dateutil

# Run Ruff
ruff check dataikuapi/iac/

# Run Black (check mode)
black --check dataikuapi/iac/

# Auto-format with Black
black dataikuapi/iac/

# Run MyPy
mypy dataikuapi/iac/ --ignore-missing-imports
```

## CI/CD Best Practices

### For Contributors

1. **Before pushing:**
   - Run tests locally: `pytest tests/iac/`
   - Check coverage: `coverage report`
   - Run linters: `ruff check dataikuapi/iac/ && black --check dataikuapi/iac/`

2. **Pull Request Guidelines:**
   - Ensure all workflows pass (green checkmarks)
   - Coverage must stay ≥85%
   - Address any linting issues
   - MyPy warnings are informational (don't block merge)

3. **If Tests Fail:**
   - Check the GitHub Actions logs
   - Download coverage artifacts if needed
   - Run tests locally with same Python version
   - Use `pytest -v --tb=short` for detailed output

### For Maintainers

**Adding New Tests:**
- Place tests in appropriate directory (unit/integration/scenarios)
- Follow existing test patterns (see `tests/iac/conftest.py`)
- Ensure coverage stays ≥85%

**Updating Dependencies:**
- Update in `setup.py` for package dependencies
- Update in workflow files for CI dependencies
- Test on all Python versions (3.8-3.11)

**Workflow Modifications:**
- Test workflow changes in a fork first
- Use `continue-on-error: true` for informational checks only
- Keep fail-fast: false for test matrix (see all failures)

## Troubleshooting

### Common Issues

**Coverage Below 85%:**
```bash
# Check which files need coverage
coverage report --show-missing

# Run coverage for specific module
pytest tests/iac/unit/test_mymodule.py --cov=dataikuapi.iac.mymodule --cov-report=term-missing
```

**Ruff Errors:**
```bash
# Auto-fix safe issues
ruff check --fix dataikuapi/iac/

# Show specific error codes
ruff check dataikuapi/iac/ --output-format=full
```

**Black Formatting:**
```bash
# See what Black would change
black --diff dataikuapi/iac/

# Apply formatting
black dataikuapi/iac/
```

**MyPy Type Errors:**
- MyPy is informational (doesn't block CI)
- Consider adding type hints incrementally
- Use `# type: ignore` for unavoidable issues

## Workflow Architecture

### Test Workflow Strategy

```
test.yml (matrix: Python 3.8, 3.9, 3.10, 3.11)
  ├─> Install dependencies
  ├─> Run unit tests (with coverage)
  ├─> Run integration tests (append coverage)
  ├─> Run scenario tests (append coverage)
  ├─> Run remaining tests (append coverage)
  ├─> Check coverage ≥85% (FAIL if below)
  ├─> Upload to Codecov (Python 3.10 only)
  └─> Archive artifacts (Python 3.10 only)
```

### Lint Workflow Strategy

```
lint.yml (single Python 3.10)
  ├─> Install linting tools
  ├─> Ruff check (FAIL on errors)
  ├─> Black check (FAIL on formatting issues)
  └─> MyPy check (informational, doesn't fail)
```

## Performance

**Typical Execution Times:**
- Test workflow: 3-5 minutes per Python version (12-20 min total)
- Lint workflow: 30-60 seconds
- Total CI time: ~15-20 minutes

**Optimization:**
- Pip caching enabled (saves ~30 seconds per job)
- Parallel matrix execution (4 versions simultaneously)
- Ruff is significantly faster than Flake8

## Coverage Reporting

Coverage reports are generated in multiple formats:

1. **Terminal output** - Visible in Actions logs
2. **XML** - For Codecov integration
3. **HTML** - Available as downloadable artifacts
4. **GitHub Step Summary** - Quick overview in Actions UI

**Accessing Coverage:**
1. Go to Actions tab
2. Click on workflow run
3. Download `coverage-reports` artifact (Python 3.10 jobs only)
4. Extract and open `htmlcov/index.html`

## Future Enhancements

Potential improvements for CI/CD:

- [ ] Add performance benchmarking workflow
- [ ] Add security scanning (Bandit, Safety)
- [ ] Add dependency vulnerability checks (Dependabot)
- [ ] Add code complexity metrics (Radon)
- [ ] Add documentation build verification
- [ ] Add release automation workflow
- [ ] Add changelog validation
- [ ] Add commit message linting (Conventional Commits)

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Black Documentation](https://black.readthedocs.io/)
- [MyPy Documentation](https://mypy.readthedocs.io/)

---

**Last Updated:** 2025-11-27
**Maintained by:** Dataiku IaC Team
