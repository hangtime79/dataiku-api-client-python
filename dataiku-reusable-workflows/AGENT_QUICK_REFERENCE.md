# Agent Quick Reference Card

**Project:** Dataiku Reusable Workflows - Discovery Agent
**Phase:** 1 - Implementation
**Approach:** TDD + Feature Branches + Code Review

---

## For All Implementation Agents

### 1. Start Your Work

```bash
# 1. Ensure you're on Reusable_Workflows branch
git checkout Reusable_Workflows
git pull origin Reusable_Workflows

# 2. Create your feature branch
git checkout -b feature/your-component-name

# 3. Create your directory structure
mkdir -p dataikuapi/iac/workflows/discovery/tests
```

### 2. TDD Workflow

```bash
# ALWAYS write tests first!

# 1. Write test (it will fail)
# 2. Run test to see it fail
pytest tests/test_your_component.py -v

# 3. Write minimal code to pass
# 4. Run test to see it pass
pytest tests/test_your_component.py -v

# 5. Refactor if needed
# 6. Run all tests
pytest tests/ -v

# 7. Check coverage
pytest tests/ --cov=dataikuapi.iac.workflows.discovery --cov-report=term-missing
```

### 3. Code Quality Checks

```bash
# Before committing, run ALL checks:

# Format code
black dataikuapi/iac/workflows/discovery/

# Lint code
ruff check dataikuapi/iac/workflows/discovery/

# Type checking (if mypy configured)
mypy dataikuapi/iac/workflows/discovery/

# Run tests
pytest tests/ -v --cov

# Ensure coverage ≥ 90%
```

### 4. Commit & Push

```bash
# Make atomic commits
git add dataikuapi/iac/workflows/discovery/your_file.py
git add dataikuapi/iac/workflows/discovery/tests/test_your_file.py
git commit -m "feat: implement YourComponent class with tests

- Add YourComponent with method1, method2
- Add 15 unit tests covering happy path and edge cases
- Coverage: 95%"

# Push to your branch
git push origin feature/your-component-name
```

### 5. Create Pull Request

Use this PR template:

```markdown
## Summary
Brief description of what this implements

## Component
Discovery Agent - [Your Component Name]

## Changes
- Implemented [ClassName] with [methods]
- Added [X] unit tests
- Coverage: [Y]%

## Testing
- [x] Unit tests added
- [x] Coverage ≥ 90%
- [x] All tests passing
- [x] Edge cases tested

## Code Quality
- [x] Black formatting applied
- [x] Ruff linting passes
- [x] Type hints added
- [x] Docstrings complete
- [x] Logging implemented

## Dependencies
[List components this depends on, or "None"]

## How to Test
```bash
pytest tests/test_your_component.py -v
```

## Checklist
- [x] Follows specification in components/discovery-agent/api-design.md
- [x] All acceptance criteria met
- [x] No breaking changes
- [x] Ready for review
```

---

## Agent-Specific Details

### Agent 1: Core Infrastructure
**Branch:** `feature/discovery-agent-core`
**Files to Create:**
- `dataikuapi/iac/workflows/discovery/__init__.py`
- `dataikuapi/iac/workflows/discovery/models.py`
- `dataikuapi/iac/workflows/discovery/exceptions.py`
- `dataikuapi/iac/workflows/discovery/tests/__init__.py`
- `dataikuapi/iac/workflows/discovery/tests/conftest.py`
- `dataikuapi/iac/workflows/discovery/tests/test_models.py`

**Reference:** `components/discovery-agent/api-design.md` - Data Models section

**Key Classes:**
- `BlockMetadata`
- `BlockPort`
- `BlockContents`
- Custom exceptions

**Tests Required:** 10+ tests for models

---

### Agent 2: Flow Crawler
**Branch:** `feature/flow-crawler`
**Files to Create:**
- `dataikuapi/iac/workflows/discovery/crawler.py`
- `dataikuapi/iac/workflows/discovery/tests/test_crawler.py`

**Reference:** `components/discovery-agent/api-design.md` - FlowCrawler section

**Key Class:** `FlowCrawler`

**Key Methods:**
- `crawl_project(project_key)`
- `get_zones()`
- `get_zone_datasets(zone)`
- `get_zone_recipes(zone)`
- `build_dependency_graph()`

**Tests Required:** 15+ tests

---

### Agent 3: Block Identifier
**Branch:** `feature/block-identifier`
**Files to Create:**
- `dataikuapi/iac/workflows/discovery/identifier.py`
- `dataikuapi/iac/workflows/discovery/tests/test_identifier.py`

**Reference:** `components/discovery-agent/api-design.md` - BlockIdentifier section

**Key Class:** `BlockIdentifier`

**Key Methods:**
- `identify_block(zone, flow_graph)`
- `is_valid_block(zone)`
- `find_inputs(zone, flow_graph)`
- `find_outputs(zone, flow_graph)`
- `classify_hierarchy(block_metadata)`

**Tests Required:** 20+ tests

---

### Agent 4: Schema Extractor
**Branch:** `feature/schema-extractor`
**Files to Create:**
- `dataikuapi/iac/workflows/discovery/schema_extractor.py`
- `dataikuapi/iac/workflows/discovery/tests/test_schema_extractor.py`

**Reference:** `components/discovery-agent/api-design.md` - SchemaExtractor section

**Key Class:** `SchemaExtractor`

**Key Methods:**
- `extract_schema(dataset)`
- `infer_schema(dataset)`
- `to_json_schema(schema)`

**Tests Required:** 10+ tests

---

### Agent 5: Catalog Writer
**Branch:** `feature/catalog-writer`
**Files to Create:**
- `dataikuapi/iac/workflows/discovery/catalog_writer.py`
- `dataikuapi/iac/workflows/discovery/tests/test_catalog_writer.py`

**Reference:** `components/discovery-agent/api-design.md` - CatalogWriter section

**Key Class:** `CatalogWriter`

**Key Methods:**
- `write_block(block_metadata, registry_project)`
- `update_index(block_metadata)`
- `create_wiki_article(block_metadata)`
- `write_schemas(port_schemas)`

**Tests Required:** 12+ tests

---

### Agent 6: CLI & Agent
**Branch:** `feature/discovery-cli`
**Files to Create:**
- `dataikuapi/iac/workflows/discovery/agent.py`
- `dataikuapi/iac/workflows/discovery/cli.py`
- `dataikuapi/iac/workflows/discovery/tests/test_agent.py`
- `dataikuapi/iac/workflows/discovery/tests/test_cli.py`

**Reference:** `components/discovery-agent/api-design.md` - DiscoveryAgent section

**Key Classes:**
- `DiscoveryAgent` (orchestrator)
- CLI functions

**Key Methods:**
- `discover(source_project, target_registry)`
- `process_zone(zone)`
- CLI argument parsing

**Tests Required:** 8+ tests

---

### Agent 7: Integration Tests
**Branch:** `feature/discovery-integration-tests`
**Files to Create:**
- `dataikuapi/iac/workflows/discovery/tests/integration/test_full_workflow.py`
- `dataikuapi/iac/workflows/discovery/tests/integration/test_multi_zone.py`
- `dataikuapi/iac/workflows/discovery/tests/integration/fixtures/mock_projects.py`

**Reference:** `components/discovery-agent/test-cases.md` - Integration Tests section

**Tests Required:** 7+ integration tests

---

## Code Review Agent

### Review Process

1. **Automated Checks First**
```bash
# Clone the PR branch
git fetch origin
git checkout feature/component-name

# Run all checks
black --check dataikuapi/iac/workflows/discovery/
ruff check dataikuapi/iac/workflows/discovery/
pytest tests/ -v --cov=dataikuapi.iac.workflows.discovery --cov-report=term-missing

# Review output
```

2. **Manual Review**
- Read the code carefully
- Check against specification
- Verify all acceptance criteria met
- Check test quality
- Look for potential issues

3. **Provide Feedback**
Use the review template from PHASE1_IMPLEMENTATION_PLAN.md

4. **Approve or Request Changes**
- APPROVE: Merge to Reusable_Workflows
- REQUEST CHANGES: Provide specific feedback
- COMMENT: Ask questions or make suggestions

---

## Common Patterns

### Test Pattern (AAA)
```python
def test_method_does_something(mock_dependency):
    """Test that method does something correctly."""
    # Arrange - set up test data
    component = Component(mock_dependency)
    input_data = {"key": "value"}

    # Act - call the method
    result = component.method(input_data)

    # Assert - verify expectations
    assert result.status == "success"
    assert result.value == "expected"
```

### Mock Pattern
```python
from unittest.mock import Mock, patch

@pytest.fixture
def mock_dss_client():
    """Mock DSSClient."""
    client = Mock()
    client.get_project.return_value = Mock(project_key="TEST")
    return client

def test_with_mock(mock_dss_client):
    """Test using mock."""
    component = Component(mock_dss_client)
    # ...
```

### Error Handling Pattern
```python
from dataikuapi.iac.workflows.discovery.exceptions import BlockNotFoundError

def get_block(self, block_id: str) -> BlockMetadata:
    """Get block by ID."""
    if block_id not in self.blocks:
        raise BlockNotFoundError(
            f"Block '{block_id}' not found. "
            f"Available: {list(self.blocks.keys())}"
        )
    return self.blocks[block_id]
```

### Logging Pattern
```python
import logging

logger = logging.getLogger(__name__)

def process(self, item):
    """Process item."""
    logger.debug(f"Processing item: {item.id}")

    try:
        result = self._do_work(item)
        logger.info(f"Successfully processed {item.id}")
        return result
    except Exception as e:
        logger.error(f"Failed to process {item.id}: {e}")
        raise
```

---

## Help & Resources

### Documentation
- Full spec: `components/discovery-agent/specification.md`
- API design: `components/discovery-agent/api-design.md`
- Test cases: `components/discovery-agent/test-cases.md`
- Implementation plan: `PHASE1_IMPLEMENTATION_PLAN.md`

### Getting Help
If stuck:
1. Review the specification for your component
2. Check existing code in `dataikuapi/iac/` for patterns
3. Review test cases for examples
4. Ask the Code Review Agent for guidance

### Useful Commands
```bash
# Run specific test
pytest tests/test_file.py::test_function_name -v

# Run with coverage
pytest --cov --cov-report=html

# View coverage report
open htmlcov/index.html

# Format all code
black .

# Lint
ruff check .

# Check test discovery
pytest --collect-only
```

---

## Success Indicators

You're ready for PR when:
- ✅ All tests passing
- ✅ Coverage ≥ 90%
- ✅ Black formatting applied
- ✅ Ruff linting passes
- ✅ Docstrings complete
- ✅ Type hints added
- ✅ All acceptance criteria met

---

**Remember:** Quality over speed. Better to take time and do it right than rush and create technical debt.
