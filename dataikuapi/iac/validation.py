"""
Validation utilities for Dataiku IaC state files.

This module provides JSON Schema validation for state files to ensure
data integrity and catch corruption early.
"""

import json
from pathlib import Path
from typing import Dict, Any

try:
    import jsonschema
    from jsonschema import ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = Exception  # Fallback

from .exceptions import StateCorruptedError


# Cache the schema to avoid repeated file reads
_SCHEMA_CACHE = None


def get_state_schema() -> Dict[str, Any]:
    """
    Load and cache the state JSON schema.

    Returns:
        The JSON schema as a dictionary
    """
    global _SCHEMA_CACHE

    if _SCHEMA_CACHE is None:
        schema_path = Path(__file__).parent / "schemas" / "state_v1.schema.json"
        with open(schema_path) as f:
            _SCHEMA_CACHE = json.load(f)

    return _SCHEMA_CACHE


def validate_state(state_data: Dict[str, Any]) -> None:
    """
    Validate state data against the JSON schema.

    Args:
        state_data: State dictionary to validate

    Raises:
        StateCorruptedError: If validation fails
        ImportError: If jsonschema is not installed

    Example:
        >>> from dataikuapi.iac.validation import validate_state
        >>> state_dict = {...}
        >>> validate_state(state_dict)  # Raises StateCorruptedError if invalid
    """
    if not JSONSCHEMA_AVAILABLE:
        raise ImportError(
            "jsonschema is required for state validation. "
            "Install with: pip install jsonschema"
        )

    schema = get_state_schema()

    try:
        jsonschema.validate(state_data, schema)
    except ValidationError as e:
        # Build a helpful error message
        error_path = " -> ".join(str(p) for p in e.path) if e.path else "root"
        raise StateCorruptedError(
            f"State validation failed at '{error_path}': {e.message}"
        ) from e


def validate_state_safe(state_data: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate state data without raising exceptions.

    Args:
        state_data: State dictionary to validate

    Returns:
        Tuple of (is_valid, error_message). error_message is empty string if valid.

    Example:
        >>> is_valid, error = validate_state_safe(state_dict)
        >>> if not is_valid:
        ...     print(f"Validation error: {error}")
    """
    if not JSONSCHEMA_AVAILABLE:
        return False, "jsonschema library not installed"

    try:
        validate_state(state_data)
        return True, ""
    except StateCorruptedError as e:
        return False, str(e)
