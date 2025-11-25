"""
Plan command for Dataiku IaC CLI.

Generates execution plan by comparing configuration against current state.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from ..config.parser import ConfigParser
from ..config.validator import ConfigValidator
from ..config.builder import DesiredStateBuilder
from ..planner.engine import PlanGenerator
from ..planner.formatter import PlanFormatter
from ..models.state import State
from ..backends.local import LocalFileBackend
from ..exceptions import (
    ConfigParseError,
    ConfigValidationError,
    BuildError,
    StateNotFoundError
)


def plan(args=None):
    """
    Generate execution plan.

    Compares configuration file against current Dataiku state
    and shows what actions would be taken.

    Examples:
        python -m dataikuapi.iac.cli.plan -c projects/customer_analytics.yml -e dev
        python -m dataikuapi.iac.cli.plan -c config/ -e prod --no-color
    """
    parser = argparse.ArgumentParser(
        description="Generate Dataiku IaC execution plan",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -c project.yml -e dev
  %(prog)s -c config/ -e prod --no-color
  %(prog)s -c project.yml --state-file custom.state.json
        """
    )

    parser.add_argument(
        "-c", "--config",
        required=True,
        help="Path to configuration file or directory"
    )

    parser.add_argument(
        "-e", "--environment",
        default="dev",
        help="Target environment (default: dev)"
    )

    parser.add_argument(
        "--state-file",
        help="Path to state file (default: .dataiku/state/{env}.state.json)"
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable color output"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    parsed_args = parser.parse_args(args)

    try:
        # Parse config
        if parsed_args.verbose:
            print("Parsing configuration...")

        config_path = Path(parsed_args.config)
        config_parser = ConfigParser()

        if config_path.is_file():
            config = config_parser.parse_file(config_path)
        elif config_path.is_dir():
            config = config_parser.parse_directory(config_path)
        else:
            print(f"Error: Config path not found: {config_path}", file=sys.stderr)
            return 1

        if parsed_args.verbose:
            print(f"✓ Parsed config for project: {config.project.key if config.project else '(no project)'}")

        # Validate config
        if parsed_args.verbose:
            print("Validating configuration...")

        validator = ConfigValidator(strict=True)
        try:
            validator.validate(config)
            if parsed_args.verbose:
                print("✓ Validation passed")
        except ConfigValidationError as e:
            print(f"Configuration validation failed:\n{e}", file=sys.stderr)
            return 1

        # Build desired state
        if parsed_args.verbose:
            print("Building desired state...")

        builder = DesiredStateBuilder(environment=parsed_args.environment)
        desired_state = builder.build(config)

        if parsed_args.verbose:
            print(f"✓ Built desired state with {len(desired_state.resources)} resources")

        # Load current state
        if parsed_args.verbose:
            print("Loading current state...")

        if parsed_args.state_file:
            state_file = Path(parsed_args.state_file)
        else:
            state_file = Path(f".dataiku/state/{parsed_args.environment}.state.json")

        backend = LocalFileBackend(state_file)
        current_state = State(environment=parsed_args.environment)

        if backend.exists():
            current_state = backend.load()
            if parsed_args.verbose:
                print(f"✓ Loaded state with {len(current_state.resources)} resources")
        else:
            if parsed_args.verbose:
                print("✓ No existing state found (will show all creates)")

        # Generate plan
        if parsed_args.verbose:
            print("Generating plan...")

        planner = PlanGenerator()
        execution_plan = planner.generate_plan(current_state, desired_state)

        if parsed_args.verbose:
            print(f"✓ Generated plan with {len(execution_plan.actions)} actions\n")

        # Format output
        formatter = PlanFormatter(color=not parsed_args.no_color)
        formatter.format(execution_plan)

        # Exit code
        # 0 = no changes, 1 = error, 2 = changes detected
        if execution_plan.has_changes():
            return 2
        else:
            return 0

    except ConfigParseError as e:
        print(f"Configuration parse error: {e}", file=sys.stderr)
        return 1
    except ConfigValidationError as e:
        print(f"Configuration validation error: {e}", file=sys.stderr)
        return 1
    except BuildError as e:
        print(f"Build error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if parsed_args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main():
    """Entry point for CLI."""
    sys.exit(plan())


if __name__ == "__main__":
    main()
