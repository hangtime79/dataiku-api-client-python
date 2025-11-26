# Dataiku IaC Test Suite

Comprehensive test suite for the Dataiku Infrastructure as Code (IaC) implementation.

## Overview

This test suite validates all IaC components through:
- **Unit tests**: Fast, mock-based tests for individual components
- **Integration tests**: Real Dataiku instance validation
- **Scenario tests**: End-to-end workflow testing
- **Performance tests**: Scale and performance validation

**Current Coverage:**
- Existing tests: 278 tests (98% pass rate)
- New tests: 50+ additional tests
- Total coverage: ~90% across all modules

---

## Test Organization

```
tests/iac/
├── pytest.ini                          # Pytest configuration
├── conftest.py                         # Shared fixtures
├── README.md                           # This file
│
├── unit/                               # FAST - Mock-based tests
│   ├── config/
│   │   └── test_validation_edge_cases.py
│   ├── state/
│   ├── planner/
│   └── sync/
│
├── integration/                        # SLOW - Real Dataiku tests
│   └── test_real_dataiku_sync.py
│
├── scenarios/                          # End-to-end workflows
│   └── test_plan_workflow.py
│
├── performance/                        # Performance & scale tests
│
└── fixtures/                           # Test data
    ├── configs/
    │   ├── simple/                    # Minimal configs
    │   ├── realistic/                 # Real-world scenarios
    │   ├── complex/                   # Complex pipelines
    │   └── edge_cases/                # Invalid/edge case configs
    └── states/                        # Sample state files
```

---

## Quick Start

### 1. Run Fast Unit Tests (Recommended for Development)

```bash
# All unit tests (mock-based, fast)
pytest -m unit

# Specific test file
pytest tests/iac/unit/config/test_validation_edge_cases.py

# With verbose output
pytest -m unit -v
```

**Run time:** ~10-30 seconds

### 2. Run Integration Tests (Requires Dataiku)

```bash
# Set environment variable to enable real Dataiku testing
export USE_REAL_DATAIKU=true

# Run integration tests
pytest -m integration

# Run specific integration test
pytest tests/iac/integration/test_real_dataiku_sync.py -v
```

**Run time:** ~1-5 minutes (depending on Dataiku instance)

### 3. Run Scenario Tests

```bash
# End-to-end workflow tests
pytest tests/iac/scenarios/

# Specific scenario
pytest tests/iac/scenarios/test_plan_workflow.py::TestSimpleProjectWorkflow
```

### 4. Run Everything

```bash
# All tests (unit + integration + scenarios)
pytest

# Skip slow tests
pytest -m "not slow"

# Only smoke tests (quick validation)
pytest -m smoke
```

---

## Test Markers

Tests are tagged with markers for selective execution:

| Marker | Purpose | Run Time |
|--------|---------|----------|
| `unit` | Fast unit tests with mocks | Seconds |
| `integration` | Real Dataiku instance tests | Minutes |
| `slow` | Performance/scale tests | Minutes |
| `smoke` | Quick smoke tests for CI/CD | Seconds |
| `edge_case` | Edge case and error handling | Seconds |
| `cleanup_required` | Creates resources needing manual cleanup | Varies |

**Usage:**

```bash
# Run only unit tests
pytest -m unit

# Run integration tests
pytest -m integration

# Run everything except slow tests
pytest -m "not slow"

# Run smoke tests only
pytest -m smoke

# Combine markers
pytest -m "unit and edge_case"
```

---

## Environment Configuration

### For Unit Tests (Mock-based)

No configuration needed - tests use mocks.

### For Integration Tests (Real Dataiku)

Set these environment variables:

```bash
# Required
export USE_REAL_DATAIKU=true

# Optional - defaults provided
export DATAIKU_HOST="http://172.18.58.26:10000"  # Default: local instance
export TEST_PROJECT_PREFIX="IAC_TEST_"            # Default: IAC_TEST_
export TEST_PROJECT_KEY="IAC_TEST_PROJECT"        # Optional: specific project to test
```

**Note:** Running on the local box, API key is NOT required.

---

## Running Specific Test Categories

### Config Validation Tests

```bash
# All validation tests
pytest tests/iac/unit/config/

# Specific edge case tests
pytest tests/iac/unit/config/test_validation_edge_cases.py::TestNamingConventionEdgeCases
```

### State Management Tests

```bash
# Existing state tests
pytest tests/iac/test_state.py

# State sync integration tests
pytest tests/iac/integration/test_real_dataiku_sync.py::TestStateManagerRealSync
```

### Plan Generation Tests

```bash
# Existing planner tests
pytest tests/iac/test_planner.py

# Scenario workflow tests
pytest tests/iac/scenarios/test_plan_workflow.py
```

### Real Dataiku Sync Tests

```bash
# All sync tests
export USE_REAL_DATAIKU=true
pytest tests/iac/integration/

# Just project sync
pytest tests/iac/integration/test_real_dataiku_sync.py::TestRealProjectSync

# Just dataset sync
pytest tests/iac/integration/test_real_dataiku_sync.py::TestRealDatasetSync
```

---

## Test Fixtures

### Config Fixtures

Located in `fixtures/configs/`:

| Fixture | Purpose | Resources |
|---------|---------|-----------|
| `simple/project.yml` | Minimal config for smoke tests | 1 project, 1 dataset |
| `realistic/customer_analytics.yml` | Real-world analytics pipeline | 1 project, 7 datasets, 4 recipes |
| `complex/ml_pipeline.yml` | Complex ML workflow | 1 project, 15+ datasets, 10+ recipes |
| `edge_cases/invalid_naming.yml` | Invalid naming conventions | Invalid config |
| `edge_cases/circular_dependency.yml` | Circular dependencies | Invalid config |

### State Fixtures

Located in `fixtures/states/`:

| Fixture | Purpose |
|---------|---------|
| `empty_state.json` | Empty state for baseline tests |
| `simple_state.json` | State with one project and dataset |

---

## Common Test Scenarios

### Test 1: Validate Config Parsing and Validation

```bash
# Test config parsing
pytest tests/iac/test_config_parser.py -v

# Test validation edge cases
pytest tests/iac/unit/config/test_validation_edge_cases.py -v
```

### Test 2: Sync State from Real Dataiku

```bash
export USE_REAL_DATAIKU=true
export TEST_PROJECT_KEY="YOUR_PROJECT_KEY"

# Sync and validate
pytest tests/iac/integration/test_real_dataiku_sync.py::TestStateManagerRealSync::test_sync_project_with_children -v -s
```

### Test 3: Generate Plan from Config

```bash
# Test plan generation workflow
pytest tests/iac/scenarios/test_plan_workflow.py::TestSimpleProjectWorkflow -v
```

### Test 4: End-to-End Workflow (Config → Plan)

```bash
# Complete workflow with simple config
pytest tests/iac/scenarios/test_plan_workflow.py::TestSimpleProjectWorkflow::test_empty_to_full_plan -v -s

# Complete workflow with realistic config
pytest tests/iac/scenarios/test_plan_workflow.py::TestRealisticPipelineWorkflow -v -s
```

---

## Continuous Integration

### Fast CI Pipeline (Unit Tests Only)

```bash
# Run in CI - fast feedback
pytest -m unit --tb=short
```

**Run time:** ~30 seconds

### Full CI Pipeline (Unit + Integration)

```bash
# Requires Dataiku instance access
export USE_REAL_DATAIKU=true
export DATAIKU_HOST="http://172.18.58.26:10000"

pytest -m "unit or integration" --tb=short
```

**Run time:** ~5 minutes

### Pre-Release Validation (Everything)

```bash
# Run all tests including slow ones
pytest --tb=short
```

**Run time:** ~10-15 minutes

---

## Debugging Failed Tests

### Verbose Output

```bash
# More detailed output
pytest -v

# Show print statements
pytest -s

# Both
pytest -v -s
```

### Specific Test

```bash
# Run single test with full output
pytest tests/iac/unit/config/test_validation_edge_cases.py::TestNamingConventionEdgeCases::test_project_key_with_lowercase_fails -v -s
```

### Debug Mode

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on first failure
pytest -x --pdb
```

### Show Fixture Setup

```bash
# Show fixture setup/teardown
pytest --setup-show
```

---

## Coverage Reports

### Generate Coverage Report

```bash
# Run tests with coverage
pytest --cov=dataikuapi.iac --cov-report=html --cov-report=term-missing

# Open HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage by Module

```bash
# Coverage for specific module
pytest tests/iac/test_config_parser.py --cov=dataikuapi.iac.config.parser --cov-report=term-missing
```

---

## Writing New Tests

### Unit Test Template

```python
import pytest
from dataikuapi.iac.config.validator import ConfigValidator

@pytest.mark.unit
class TestMyFeature:
    """Test my new feature"""

    def test_basic_functionality(self):
        """Test basic use case"""
        validator = ConfigValidator()
        # Test logic here
        assert True

    def test_edge_case(self):
        """Test edge case"""
        # Edge case logic
        assert True
```

### Integration Test Template

```python
import pytest

@pytest.mark.integration
@pytest.mark.slow
class TestMyIntegration:
    """Test with real Dataiku"""

    def test_with_real_instance(self, real_client, skip_if_no_real_dataiku):
        """Test against real Dataiku"""
        try:
            # Test logic using real_client
            assert True
        except Exception as e:
            pytest.skip(f"Test failed: {e}")
```

---

## Troubleshooting

### Issue: Integration tests skipped

**Cause:** `USE_REAL_DATAIKU` not set

**Solution:**
```bash
export USE_REAL_DATAIKU=true
pytest -m integration
```

### Issue: Connection errors to Dataiku

**Cause:** Dataiku instance not accessible or wrong host

**Solution:**
```bash
# Verify host is correct
export DATAIKU_HOST="http://172.18.58.26:10000"

# Test connection
pytest tests/iac/integration/test_real_dataiku_sync.py::TestConnectionAndAuth::test_client_can_connect -v -s
```

### Issue: Test project not found

**Cause:** Test project doesn't exist in Dataiku

**Solution:**
```bash
# Use existing project
export TEST_PROJECT_KEY="YOUR_EXISTING_PROJECT"

# Or tests will skip if project not found
```

### Issue: Circular import errors

**Cause:** PYTHONPATH not set correctly

**Solution:**
```bash
# Run from repository root
cd /opt/dataiku/dss_install/dataiku-api-client-python
pytest
```

---

## Performance Benchmarks

Expected test execution times:

| Test Suite | Count | Time |
|------------|-------|------|
| Unit tests (mock-based) | ~200 | ~30s |
| Integration tests (real Dataiku) | ~20 | ~2m |
| Scenario tests | ~15 | ~1m |
| **Total** | **~235** | **~3m** |

**Note:** Times vary based on system and Dataiku instance performance.

---

## Next Steps

### Additional Tests to Add

1. **Performance Tests**
   - Large config files (100+ resources)
   - State file size performance
   - Sync performance benchmarks

2. **CLI Tests**
   - All CLI flags and combinations
   - Error messages and exit codes
   - Output validation

3. **State Corruption Tests**
   - Recovery from corrupted state files
   - Version migration
   - Backup/restore

4. **Apply Execution Tests** (Week 3)
   - Resource creation
   - Resource updates
   - Resource deletion
   - Rollback on failure

---

## Resources

- **Documentation:** `../../docs/IAC_OVERVIEW.md`
- **Planning Docs:** `../../dataiku-iac-planning/`
- **Demo Scripts:** `../../demos/week2_plan_workflow.py`
- **IaC Source:** `../../dataikuapi/iac/`

---

## Contributing

When adding new tests:

1. Follow existing patterns (see templates above)
2. Use appropriate markers (`@pytest.mark.unit`, `@pytest.mark.integration`, etc.)
3. Add docstrings explaining test purpose
4. Use fixtures from `conftest.py`
5. Update this README if adding new test categories

---

**Last Updated:** 2025-11-26
**Test Suite Version:** 2.0
**IaC Version:** Week 2 (Plan Generation)
