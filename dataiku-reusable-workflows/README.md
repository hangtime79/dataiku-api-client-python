# Dataiku Reusable Workflows System

## Overview

This directory contains the complete planning, specifications, and test definitions for the Dataiku Reusable Workflows System. The system enables enterprise data science teams to shift from project-based delivery to component-based composition.

**Status:** Planning Phase (TDD)
**Target:** AI Agent Implementation

---

## The Problem

Enterprise data science teams deliver projects, not capabilities. Each new project rebuilds similar pipelines from scratch. Code gets reused, but workflows don't. The goal is to enable:

1. **Workflow Reuse** - Reuse configured, wired, tested pipelines (not just code snippets)
2. **Reference Without Cloning** - Access the same pipeline rather than managing copies
3. **Multi-Model Orchestration** - Stitch 6-7 models into orchestrated solutions
4. **Granular Reusability** - Consume blocks in parts (just data prep, not full model)
5. **Hierarchical Components** - Compose from sensor → equipment → process → plant → business
6. **Extension Without Modification** - Extend blocks without affecting other consumers

---

## Core Concepts

### Block

A **Block** is a Flow Zone containing datasets, recipes, and optionally models, with defined input/output boundaries. Blocks are the unit of reuse.

### Solution Block

A **Solution Block** is a special block type that orchestrates multiple model blocks in sequence or via dependency resolution.

### Registry

The **BLOCKS_REGISTRY** is a dedicated Dataiku project that serves as the central catalog of all published blocks. Individual projects reference blocks from the registry.

### Extension Model

Blocks support two extension patterns:
1. **Python Inheritance** - Class inheritance in project libraries
2. **Recipe Override** - Replace a recipe with a custom implementation having the same I/O

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Claude Code  │  │    Codex     │  │    Gemini CLI        │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         └─────────────────┼─────────────────────┘              │
│                           ▼                                     │
├─────────────────────────────────────────────────────────────────┤
│                      Agent Layer                                │
│  ┌─────────────────────┐    ┌─────────────────────────────┐    │
│  │   Discovery Agent   │    │      Executing Agent        │    │
│  │  (Crawl → Catalog)  │    │  (Intent → Plan → Apply)    │    │
│  └──────────┬──────────┘    └──────────────┬──────────────┘    │
│             │                              │                    │
│             ▼                              ▼                    │
├─────────────────────────────────────────────────────────────────┤
│                      Catalog Layer                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              BLOCKS_REGISTRY Project                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │   │
│  │  │    Wiki     │  │   Library   │  │     Bundles     │  │   │
│  │  │  (Human)    │  │   (JSON)    │  │   (Versions)    │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                      Engine Layer                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           IaC Engine (Extended for Blocks)               │   │
│  │     Config → Validate → Plan → Apply                     │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                      Dataiku Layer                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Dataiku DSS API                         │   │
│  │  Projects | Datasets | Recipes | Zones | Wiki | Models   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Document Navigation

### Architecture Documents (5 docs)

| Document | Description |
|----------|-------------|
| [01-overview.md](architecture/01-overview.md) | System architecture, layers, component interactions |
| [02-block-model.md](architecture/02-block-model.md) | Block definition, types, lifecycle, validation |
| [03-registry.md](architecture/03-registry.md) | BLOCKS_REGISTRY project design, operations |
| [04-inheritance.md](architecture/04-inheritance.md) | Extension patterns (class, recipe, composition) |
| [05-solution-blocks.md](architecture/05-solution-blocks.md) | Multi-model orchestration, dependency resolution |

### Component Specifications (3 components)

| Component | Files | Status |
|-----------|-------|--------|
| [discovery-agent/](components/discovery-agent/) | specification.md, api-design.md, test-cases.md | Complete |
| [executing-agent/](components/executing-agent/) | specification.md, api-design.md, test-cases.md | Complete |
| [iac-extension/](components/iac-extension/) | specification.md, api-design.md, test-cases.md | Complete |

### JSON Schemas (4 schemas)

| Schema | Purpose |
|--------|---------|
| [block-reference.schema.json](schemas/block-reference.schema.json) | Block references in IaC config |
| [block-manifest.schema.json](schemas/block-manifest.schema.json) | Block manifests in registry |
| [catalog-index.schema.json](schemas/catalog-index.schema.json) | Catalog index file format |
| [iac-config.schema.json](schemas/iac-config.schema.json) | IaC config with block support |

### Example Configurations (6 examples)

| Example | Description | Complexity |
|---------|-------------|------------|
| [01-simple-block.yaml](examples/01-simple-block.yaml) | Single block with basic I/O | Beginner |
| [02-chained-blocks.yaml](examples/02-chained-blocks.yaml) | Multiple blocks in sequence | Beginner |
| [03-block-with-recipe-override.yaml](examples/03-block-with-recipe-override.yaml) | Custom recipe replacement | Intermediate |
| [04-block-with-class-extension.yaml](examples/04-block-with-class-extension.yaml) | Class injection | Intermediate |
| [05-multi-instance-blocks.yaml](examples/05-multi-instance-blocks.yaml) | Same block, multiple instances | Intermediate |
| [06-solution-block.yaml](examples/06-solution-block.yaml) | Multi-block solution | Advanced |

### Supporting Documents

| Resource | Description |
|----------|-------------|
| [PLANNING_SUMMARY.md](PLANNING_SUMMARY.md) | Initial planning session summary |
| [tests/](tests/) | Test case definitions (TDD) |

---

## Implementation Phases

### Phase 1: Discovery Agent
**Goal:** Crawl projects and build the block catalog

- Zone-based block detection
- Input/output boundary identification
- Wiki catalog writer (hierarchical)
- Library JSON index writer
- Schema extraction
- Merge logic for manual edits

### Phase 2: IaC Block Extension
**Goal:** Add block support to existing IaC engine

- BlockConfig model (zone-based)
- SolutionConfig model (multi-model)
- Configurable hierarchy
- Extension/inheritance support
- Block validation rules
- Integration with existing IaC

### Phase 3: Executing Agent
**Goal:** Match intent to blocks and generate plans

- Catalog reader (Wiki + Library)
- Block matching logic
- Wiring/composition engine
- Config generator
- Intent parsing

### Phase 4: Plan/Apply for Blocks
**Goal:** Deploy composed blocks as projects

- Zone instantiation
- Recipe inheritance/override
- Cross-block wiring
- Single project deployment
- Bundle snapshot creation

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Block granularity | Flow Zone | Natural boundary with defined I/O |
| Registry model | Centralized BLOCKS_REGISTRY | Single source of truth, projects reference it |
| Extension model | Both Python inheritance + Recipe override | Maximum flexibility |
| Hierarchy | Organization-configurable | Different orgs have different taxonomies |
| Catalog storage | Wiki (human) + Library (JSON) | Human-editable + machine-parseable |
| Versioning | Semantic + Bundle snapshots | Industry standard + immutable releases |
| Solution sequencing | Explicit + Dependency resolution | Support both known and dynamic ordering |

---

## Integration with Existing IaC

This system builds on the existing IaC implementation (Waves 1-3). Key integration points:

1. **Config Parsing** - Extend parser for `blocks:` and `solutions:` sections
2. **Validation** - Add block reference validation, hierarchy validation
3. **State Management** - Track instantiated blocks in state
4. **Plan Generation** - Include block operations in plan output
5. **Apply Execution** - Leverage Wave 4 apply for block deployment

See [iac-extension/](components/iac-extension/) for detailed integration specs.

---

## For Implementing Agents

**Important:** These documents are written for AI agents to implement. Each component specification includes:

1. **Clear interfaces** - Input/output contracts
2. **Step-by-step logic** - Explicit algorithms
3. **Test cases** - TDD-style test definitions
4. **Error handling** - Expected failure modes
5. **Dependencies** - Required imports and setup

Agents should:
- Read the specification completely before implementing
- Write tests first (TDD)
- Follow the interfaces exactly as specified
- Handle all documented error cases
- Not add features beyond the specification

---

## Documentation Completeness

| Category | Items | Status |
|----------|-------|--------|
| Architecture Docs | 5 documents | Complete |
| Discovery Agent | spec, api-design, test-cases | Complete |
| Executing Agent | spec, api-design, test-cases | Complete |
| IaC Extension | spec, api-design, test-cases | Complete |
| JSON Schemas | 4 schemas | Complete |
| Example Configs | 6 examples | Complete |

**Total Documentation:** 26 files covering all aspects of the system.

---

## Version

- **Document Version:** 1.1.0
- **Last Updated:** 2025-11-28
- **Status:** Planning Complete - Ready for Implementation
