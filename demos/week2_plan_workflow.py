#!/usr/bin/env python3
"""
Week 2 Demo: Plan Workflow

Demonstrates:
1. Parsing YAML config
2. Validating config
3. Building desired state
4. Generating plan
5. Formatting plan output
"""

from pathlib import Path
from dataikuapi.iac.config.parser import ConfigParser
from dataikuapi.iac.config.validator import ConfigValidator
from dataikuapi.iac.config.builder import DesiredStateBuilder
from dataikuapi.iac.planner.engine import PlanGenerator
from dataikuapi.iac.planner.formatter import PlanFormatter
from dataikuapi.iac.models.state import State


def main():
    print("=" * 60)
    print("Week 2 Demo: Plan Workflow")
    print("=" * 60)
    print()

    # 1. Parse config
    print("Step 1: Parsing configuration...")
    print("-" * 60)
    parser = ConfigParser()
    config = parser.parse_file("tests/iac/fixtures/config_simple.yml")
    print(f"✓ Parsed config for project: {config.project.key}")
    print(f"  - Project: {config.project.name}")
    print(f"  - Datasets: {len(config.datasets)}")
    print(f"  - Recipes: {len(config.recipes)}")
    print()

    # 2. Validate config
    print("Step 2: Validating configuration...")
    print("-" * 60)
    validator = ConfigValidator()
    try:
        validator.validate(config)
        print("✓ Validation passed (0 errors)")
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return 1
    print()

    # 3. Build desired state
    print("Step 3: Building desired state...")
    print("-" * 60)
    builder = DesiredStateBuilder(environment="demo")
    desired_state = builder.build(config)
    print(f"✓ Built desired state with {len(desired_state.resources)} resources")
    for resource in desired_state.resources.values():
        print(f"  - {resource.resource_id} ({resource.resource_type})")
    print()

    # 4. Generate plan (empty current state = all creates)
    print("Step 4: Generating plan (empty current state)...")
    print("-" * 60)
    current_state = State(environment="demo")
    planner = PlanGenerator()
    plan = planner.generate_plan(current_state, desired_state)
    print(f"✓ Generated plan with {len(plan.actions)} actions")
    print()

    # 5. Format plan
    print("Step 5: Plan output:")
    print("-" * 60)
    formatter = PlanFormatter(color=True)
    formatter.format(plan)
    print()

    # 6. Demonstrate no-change scenario
    print("Step 6: Generating plan (matching states = no changes)...")
    print("-" * 60)
    plan2 = planner.generate_plan(desired_state, desired_state)
    print(f"✓ Generated plan with {len(plan2.actions)} actions")
    print()
    formatter.format(plan2)
    print()

    # 7. Demonstrate update scenario
    print("Step 7: Generating plan (modified state = updates)...")
    print("-" * 60)

    # Create a modified version of desired state
    modified_state = State(environment="demo")
    for resource_id, resource in desired_state.resources.items():
        # Create modified resource
        modified_resource = resource
        if resource.resource_type == "project":
            # Change project description
            modified_attrs = resource.attributes.copy()
            modified_attrs["description"] = "Modified description"
            from dataikuapi.iac.models.state import Resource, ResourceMetadata
            modified_resource = Resource(
                resource_id=resource.resource_id,
                resource_type=resource.resource_type,
                attributes=modified_attrs,
                metadata=resource.metadata
            )
        modified_state.add_resource(modified_resource)

    plan3 = planner.generate_plan(desired_state, modified_state)
    print(f"✓ Generated plan with {len(plan3.actions)} actions")
    print()
    formatter.format(plan3)
    print()

    print("=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print()
    print("Summary:")
    print(f"  - Config parsing: ✓")
    print(f"  - Config validation: ✓")
    print(f"  - State building: ✓")
    print(f"  - Plan generation: ✓")
    print(f"  - Plan formatting: ✓")
    print()
    print("Week 2 (Plan Generation) implementation is working correctly!")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
