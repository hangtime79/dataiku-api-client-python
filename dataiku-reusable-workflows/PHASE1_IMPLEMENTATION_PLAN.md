# Phase 1: Discovery Agent Implementation Plan

**Status:** Ready to Execute
**Approach:** Multi-Agent Parallel Development with Code Review
**Methodology:** TDD + Feature Branches + PR Reviews

---

## Overview

The Discovery Agent will be built by **6 specialized implementation agents** working in parallel on separate feature branches, plus **1 code review agent** ensuring quality. Each agent is responsible for:

1. Creating their feature branch
2. Writing unit tests FIRST (TDD)
3. Implementing the component
4. Ensuring tests pass
5. Creating a PR for review
6. Addressing review feedback

---

## Git Workflow

### Branch Strategy

```
Reusable_Workflows (current branch)
    │
    ├── feature/discovery-agent-core
    ├── feature/flow-crawler
    ├── feature/block-identifier
    ├── feature/schema-extractor
    ├── feature/catalog-writer
    ├── feature/discovery-cli
    └── feature/discovery-integration-tests
```

### Merge Order (Dependency-Based)

```
1. discovery-agent-core        (base classes, no dependencies)
2. flow-crawler               (depends on: core)
3. block-identifier           (depends on: core, flow-crawler)
4. schema-extractor           (depends on: core, flow-crawler)
5. catalog-writer             (depends on: core)
6. discovery-cli              (depends on: all above)
7. discovery-integration-tests (depends on: all above)
```

---

## Agent Assignments

### Agent 1: Core Infrastructure Agent
**Branch:** `feature/discovery-agent-core`
**Priority:** P0 (blocking others)
**Estimated Complexity:** Medium

**Responsibilities:**
- Create base directory structure
- Implement base classes and data models
- Create shared utilities
- Set up test infrastructure

**Deliverables:**
```
dataikuapi/iac/workflows/discovery/
├── __init__.py
├── models.py                 # BlockMetadata, BlockPort, etc.
├── exceptions.py             # Custom exceptions
└── tests/
    ├── __init__.py
    ├── conftest.py          # Shared fixtures
    └── test_models.py       # Model tests
```

**Test Coverage Required:** 95%+

**Acceptance Criteria:**
- [ ] All data models implemented (BlockMetadata, BlockPort, BlockContents)
- [ ] All custom exceptions defined
- [ ] Shared fixtures created (mock_client, mock_project, mock_flow)
- [ ] Type hints on all classes/methods
- [ ] Docstrings on all public APIs
- [ ] All unit tests passing
- [ ] No linting errors (ruff, black)

---

### Agent 2: Flow Crawler Agent
**Branch:** `feature/flow-crawler`
**Priority:** P1 (blocks identifier & extractor)
**Estimated Complexity:** High

**Responsibilities:**
- Implement FlowCrawler class
- Zone traversal logic
- Dataset/recipe enumeration
- Dependency graph construction

**Deliverables:**
```
dataikuapi/iac/workflows/discovery/
├── crawler.py               # FlowCrawler class
└── tests/
    └── test_crawler.py      # Crawler tests
```

**Test Cases Required:** 15+ (from test-cases.md)
- Crawl single zone
- Crawl multi-zone project
- Handle empty zones
- Handle cross-zone dependencies
- Handle external datasets
- Error handling (project not found, etc.)

**Acceptance Criteria:**
- [ ] FlowCrawler class implemented per API design
- [ ] Can traverse all zones in a project
- [ ] Correctly identifies datasets and recipes in each zone
- [ ] Builds dependency graph between datasets
- [ ] Handles edge cases (empty zones, external refs)
- [ ] All 15+ unit tests passing
- [ ] Integration test with mock Dataiku project
- [ ] Performance: Can crawl 50-zone project in <10s

---

### Agent 3: Block Identifier Agent
**Branch:** `feature/block-identifier`
**Priority:** P1 (parallel with crawler)
**Estimated Complexity:** High

**Responsibilities:**
- Implement BlockIdentifier class
- Input/output boundary detection
- Block validation logic
- Block metadata extraction

**Deliverables:**
```
dataikuapi/iac/workflows/discovery/
├── identifier.py            # BlockIdentifier class
└── tests/
    └── test_identifier.py   # Identifier tests
```

**Test Cases Required:** 20+ (from test-cases.md)
- Identify valid zone as block
- Reject zone without inputs
- Reject zone without outputs
- Identify multiple inputs/outputs
- Handle optional inputs
- Detect containment violations
- Classify hierarchy level
- Extract tags

**Acceptance Criteria:**
- [ ] BlockIdentifier class implemented per API design
- [ ] Correctly identifies valid blocks (inputs + outputs)
- [ ] Rejects invalid blocks with clear error messages
- [ ] Extracts all required metadata fields
- [ ] Classifies hierarchy level correctly
- [ ] Extracts domain and tags
- [ ] All 20+ unit tests passing
- [ ] Edge case handling (shared datasets, external refs)

---

### Agent 4: Schema Extractor Agent
**Branch:** `feature/schema-extractor`
**Priority:** P2 (can run in parallel)
**Estimated Complexity:** Medium

**Responsibilities:**
- Implement SchemaExtractor class
- Dataset schema extraction
- Schema inference for untyped data
- Schema validation

**Deliverables:**
```
dataikuapi/iac/workflows/discovery/
├── schema_extractor.py      # SchemaExtractor class
└── tests/
    └── test_schema_extractor.py
```

**Test Cases Required:** 10+ (from test-cases.md)
- Extract schema from SQL dataset
- Extract schema from managed dataset
- Infer schema from sample data
- Handle missing schemas
- Validate schema format
- Convert to JSON schema format

**Acceptance Criteria:**
- [ ] SchemaExtractor class implemented per API design
- [ ] Extracts schemas from all dataset types
- [ ] Infers schemas when not explicitly defined
- [ ] Converts to standard JSON schema format
- [ ] Handles schema-less datasets gracefully
- [ ] All 10+ unit tests passing
- [ ] Validates extracted schemas

---

### Agent 5: Catalog Writer Agent
**Branch:** `feature/catalog-writer`
**Priority:** P2 (parallel with extractor)
**Estimated Complexity:** Medium-High

**Responsibilities:**
- Implement CatalogWriter class
- Wiki article generation
- JSON index updates
- Merge logic for existing entries

**Deliverables:**
```
dataikuapi/iac/workflows/discovery/
├── catalog_writer.py        # CatalogWriter class
└── tests/
    └── test_catalog_writer.py
```

**Test Cases Required:** 12+ (from test-cases.md)
- Write new block to catalog
- Update existing block
- Preserve manual edits in wiki
- Update JSON index atomically
- Handle concurrent writes
- Create schema files
- Organize by hierarchy

**Acceptance Criteria:**
- [ ] CatalogWriter class implemented per API design
- [ ] Creates wiki articles with correct format
- [ ] Updates JSON index without losing existing entries
- [ ] Preserves manual edits (merge logic)
- [ ] Writes schema files to library
- [ ] Organizes by hierarchy and domain
- [ ] All 12+ unit tests passing
- [ ] Atomic writes (temp + rename pattern)

---

### Agent 6: CLI & Integration Agent
**Branch:** `feature/discovery-cli`
**Priority:** P3 (depends on all above)
**Estimated Complexity:** Medium

**Responsibilities:**
- Implement CLI interface
- Orchestrate discovery workflow
- Progress reporting
- Error handling and user feedback

**Deliverables:**
```
dataikuapi/iac/workflows/discovery/
├── cli.py                   # CLI interface
├── agent.py                 # DiscoveryAgent orchestrator
└── tests/
    ├── test_cli.py
    └── test_agent.py
```

**Test Cases Required:** 8+ (from test-cases.md)
- CLI argument parsing
- Full discovery workflow
- Progress reporting
- Error handling
- Dry-run mode
- Force overwrite mode

**Acceptance Criteria:**
- [ ] CLI interface with argparse
- [ ] DiscoveryAgent orchestrates all components
- [ ] Progress bar/logging
- [ ] Proper error messages
- [ ] --dry-run flag works
- [ ] --force flag works
- [ ] All 8+ unit tests passing
- [ ] Help text complete and accurate

---

### Agent 7: Integration Testing Agent
**Branch:** `feature/discovery-integration-tests`
**Priority:** P4 (final validation)
**Estimated Complexity:** High

**Responsibilities:**
- Create end-to-end integration tests
- Test against mock Dataiku instance
- Test against real Dataiku (if available)
- Performance testing

**Deliverables:**
```
dataikuapi/iac/workflows/discovery/
└── tests/
    ├── integration/
    │   ├── __init__.py
    │   ├── test_full_workflow.py
    │   ├── test_multi_zone_project.py
    │   ├── test_catalog_updates.py
    │   └── fixtures/
    │       ├── mock_projects.py
    │       └── sample_configs.py
    └── performance/
        └── test_performance.py
```

**Test Cases Required:** 7+ (from test-cases.md)
- Full workflow: crawl → identify → catalog
- Multi-zone project discovery
- Catalog update (existing blocks)
- Error recovery
- Performance benchmark

**Acceptance Criteria:**
- [ ] All integration tests passing
- [ ] Tests work with mock Dataiku
- [ ] Tests work with real Dataiku (if available)
- [ ] Performance tests meet benchmarks
- [ ] Coverage report generated
- [ ] All edge cases tested

---

## Code Review Agent

### Agent 8: Code Review & QA Agent
**Role:** Quality Gatekeeper
**Responsibilities:** Review all PRs before merge

**Review Checklist for Each PR:**

#### Code Quality
- [ ] Follows Python style guide (PEP 8)
- [ ] Black formatting applied
- [ ] Ruff linting passes with no errors
- [ ] Type hints on all functions/methods
- [ ] Docstrings on all public APIs (Google style)
- [ ] No commented-out code
- [ ] No print statements (use logging)

#### Testing
- [ ] All unit tests passing
- [ ] Test coverage ≥ 90% for new code
- [ ] Tests follow AAA pattern (Arrange, Act, Assert)
- [ ] Edge cases tested
- [ ] Error paths tested
- [ ] Mocks used appropriately (no real API calls in unit tests)

#### Design
- [ ] Follows SOLID principles
- [ ] No circular dependencies
- [ ] Appropriate abstraction levels
- [ ] Error handling comprehensive
- [ ] No hardcoded values (use config/constants)
- [ ] Logging at appropriate levels

#### Documentation
- [ ] Code is self-documenting
- [ ] Complex logic has comments
- [ ] README updated if needed
- [ ] API changes documented

#### Integration
- [ ] No breaking changes to existing code
- [ ] Dependencies properly declared
- [ ] Imports organized (stdlib, third-party, local)
- [ ] No merge conflicts

**Actions:**
- **APPROVE** - If all criteria met
- **REQUEST CHANGES** - If issues found (with specific feedback)
- **COMMENT** - For suggestions/questions

---

## Implementation Sequence

### Week 1: Foundation
**Days 1-2:**
- Agent 1: Core Infrastructure (P0)
- Review & Merge to `Reusable_Workflows`

**Days 3-5:**
- Agent 2: Flow Crawler (P1)
- Agent 3: Block Identifier (P1)
- Agent 4: Schema Extractor (P2)
- Reviews & Merges

### Week 2: Integration
**Days 6-8:**
- Agent 5: Catalog Writer (P2)
- Agent 6: CLI & Agent (P3)
- Reviews & Merges

**Days 9-10:**
- Agent 7: Integration Tests (P4)
- Final review & merge
- Full test suite execution

---

## Quality Gates

### Per-Component Gates
Each component must pass before PR approval:
1. All unit tests passing (`pytest tests/`)
2. Code coverage ≥ 90% (`pytest --cov`)
3. Linting passes (`ruff check .`)
4. Formatting applied (`black .`)
5. Type checking passes (`mypy`)
6. Documentation complete

### Integration Gate
Before merging to main:
1. All components integrated
2. Integration tests passing
3. Performance benchmarks met
4. Example usage documented
5. No regressions in existing tests

---

## Testing Standards

### Unit Test Requirements
- **Coverage:** ≥ 90% for new code
- **Isolation:** Use mocks for external dependencies
- **Speed:** Unit tests run in < 5 seconds
- **Clarity:** Tests are documentation

### Test Organization
```python
# test_component.py

class TestComponentName:
    """Test suite for ComponentName class."""

    def test_happy_path_scenario(self):
        """Test normal operation."""
        # Arrange
        # Act
        # Assert
        pass

    def test_edge_case_scenario(self):
        """Test edge case."""
        pass

    def test_error_handling(self):
        """Test error conditions."""
        pass
```

### Fixtures (conftest.py)
```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_dss_client():
    """Mock DSSClient for testing."""
    client = Mock()
    # Configure mock
    return client

@pytest.fixture
def mock_project():
    """Mock DSSProject for testing."""
    project = Mock()
    # Configure mock
    return project
```

---

## Coding Standards

### Import Organization
```python
# 1. Standard library
import json
from typing import Dict, List
from dataclasses import dataclass

# 2. Third-party
import pytest
from dataikuapi import DSSClient

# 3. Local/package
from dataikuapi.iac.workflows.discovery.models import BlockMetadata
from dataikuapi.iac.workflows.discovery.exceptions import BlockNotFoundError
```

### Docstring Format (Google Style)
```python
def identify_block(self, zone, flow_graph: Dict) -> BlockMetadata:
    """
    Identify if a zone is a valid block and extract metadata.

    Args:
        zone: Dataiku zone object
        flow_graph: Flow dependency graph

    Returns:
        BlockMetadata object with block information

    Raises:
        InvalidBlockError: If zone is not a valid block

    Example:
        >>> identifier = BlockIdentifier(client)
        >>> metadata = identifier.identify_block(zone, graph)
        >>> print(metadata.block_id)
        'FEATURE_ENGINEERING'
    """
```

### Error Handling
```python
# Always provide context in exceptions
try:
    block = self.get_block(block_id)
except KeyError:
    raise BlockNotFoundError(
        f"Block '{block_id}' not found in registry. "
        f"Available blocks: {list(self.blocks.keys())}"
    )
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate levels
logger.debug(f"Processing zone: {zone.name}")
logger.info(f"Discovered {len(blocks)} blocks")
logger.warning(f"Zone '{zone.name}' has no outputs, skipping")
logger.error(f"Failed to process zone: {error}")
```

---

## Communication Protocol

### PR Description Template
```markdown
## Summary
Brief description of changes

## Component
Which agent/component this implements

## Testing
- [ ] Unit tests added/updated
- [ ] Coverage ≥ 90%
- [ ] All tests passing

## Checklist
- [ ] Code follows style guide
- [ ] Docstrings added
- [ ] Type hints added
- [ ] Logging implemented
- [ ] Error handling complete

## Dependencies
List any components this depends on

## Breaking Changes
None / List any breaking changes
```

### Review Feedback Format
```markdown
## Review: feature/component-name

### Approval Status
- [ ] APPROVE
- [x] REQUEST CHANGES
- [ ] COMMENT

### Issues Found
1. **Critical:** Missing error handling in method X (line 45)
2. **Major:** Test coverage only 75% (target: 90%)
3. **Minor:** Docstring missing for private method _helper

### Suggestions
- Consider extracting lines 100-120 into separate method
- Add logging at INFO level for main operations

### Action Required
Please address items 1-2 before re-review.
```

---

## Success Criteria

### Component Level
✅ Each component must:
- Pass all unit tests (100% of test cases)
- Meet coverage targets (≥ 90%)
- Pass code review
- Have complete documentation
- Follow coding standards

### Integration Level
✅ Full Discovery Agent must:
- Successfully discover blocks in test projects
- Write correct catalog entries
- Handle errors gracefully
- Meet performance targets
- Pass all integration tests

### Quality Level
✅ Overall quality:
- Zero critical bugs
- All acceptance criteria met
- Code review approved
- Documentation complete
- Ready for production use

---

## Risk Mitigation

### Risk: Component Dependencies Block Progress
**Mitigation:** Clear dependency order, P0 items first, parallel work where possible

### Risk: Test Coverage Insufficient
**Mitigation:** TDD approach, coverage gates in PR reviews, automated coverage reports

### Risk: Integration Issues
**Mitigation:** Integration tests in separate branch, early integration attempts, clear interfaces

### Risk: Code Quality Issues
**Mitigation:** Automated linting, code review agent, clear coding standards

---

## Deliverables Checklist

By end of Phase 1, we will have:

- [x] Core infrastructure and models
- [x] Flow crawler implementation
- [x] Block identifier implementation
- [x] Schema extractor implementation
- [x] Catalog writer implementation
- [x] CLI interface
- [x] 75+ unit tests passing
- [x] 7+ integration tests passing
- [x] Code coverage ≥ 90%
- [x] All code reviewed and approved
- [x] Documentation complete
- [x] Ready for Phase 2 (IaC Extension)

---

## Next Steps

1. **Create all feature branches** from `Reusable_Workflows`
2. **Assign agents** to their respective components
3. **Agent 1 starts immediately** (P0 - core infrastructure)
4. **Other agents start** after dependencies met
5. **Code Review Agent** monitors all PRs
6. **Integration Agent** starts when all components ready

---

**Last Updated:** 2025-11-28
**Status:** Ready to Execute
**Estimated Duration:** 10 days with parallel execution
