# Test Suite Setup Guide

Quick setup guide for running the Dataiku IaC test suite.

## Prerequisites

- Python 3.10+
- Access to Dataiku instance (for integration tests)
- Repository cloned locally

## Installation

### Option 1: Install pytest globally

```bash
pip3 install pytest pytest-cov
```

### Option 2: Use virtual environment (recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install pytest pytest-cov

# Install Dataiku API client in development mode
pip install -e .
```

### Option 3: Install all development dependencies

```bash
# If you have a requirements-dev.txt
pip install -r requirements-dev.txt

# Or create one
cat > requirements-dev.txt <<EOF
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
EOF

pip install -r requirements-dev.txt
```

## Verify Installation

```bash
# Check pytest is installed
pytest --version

# Run a simple smoke test
pytest tests/iac/unit/config/test_validation_edge_cases.py::TestNamingConventionEdgeCases::test_project_key_with_numbers_allowed -v
```

## Environment Configuration

### For Unit Tests Only

No configuration needed - unit tests use mocks.

### For Integration Tests

```bash
# Required for integration tests
export USE_REAL_DATAIKU=true

# Optional - use defaults if not set
export DATAIKU_HOST="http://172.18.58.26:10000"
export TEST_PROJECT_PREFIX="IAC_TEST_"
```

## Quick Test Run

```bash
# Fast unit tests only
pytest -m unit

# All tests
pytest
```

## Troubleshooting

### pytest not found

**Issue:** `bash: pytest: command not found` or `No module named pytest`

**Solution:**
```bash
pip3 install pytest
# or
python3 -m pip install pytest
```

### Import errors

**Issue:** `ModuleNotFoundError: No module named 'dataikuapi'`

**Solution:**
```bash
# Install package in development mode
pip install -e .

# Or set PYTHONPATH
export PYTHONPATH=/opt/dataiku/dss_install/dataiku-api-client-python:$PYTHONPATH
```

### Permission errors

**Issue:** Permission denied when installing packages

**Solution:**
```bash
# Install for user only
pip3 install --user pytest pytest-cov

# Or use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install pytest pytest-cov
```

## Next Steps

After setup, see [README.md](README.md) for:
- Running specific test categories
- Test markers and organization
- Writing new tests
- CI/CD integration

---

**Quick Reference:**

```bash
# Install
pip3 install pytest pytest-cov

# Unit tests (fast)
pytest -m unit

# Integration tests (needs Dataiku)
export USE_REAL_DATAIKU=true
pytest -m integration

# All tests
pytest
```
