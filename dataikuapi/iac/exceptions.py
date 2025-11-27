"""
Custom exceptions for Dataiku IaC module.
"""


class DataikuIaCError(Exception):
    """Base exception for Dataiku IaC"""
    pass


class StateNotFoundError(DataikuIaCError):
    """State file doesn't exist"""
    pass


class StateCorruptedError(DataikuIaCError):
    """State file is invalid"""
    pass


class StateWriteError(DataikuIaCError):
    """Failed to write state"""
    pass


class ResourceNotFoundError(DataikuIaCError):
    """Resource doesn't exist in Dataiku"""
    pass


class ConfigParseError(DataikuIaCError):
    """Configuration file parsing error"""
    pass


class ConfigValidationError(DataikuIaCError):
    """Configuration validation error"""

    def __init__(self, errors):
        """
        Initialize with list of validation errors.

        Args:
            errors: List of ValidationError objects or single error message
        """
        if isinstance(errors, list):
            self.errors = errors
            error_msgs = [f"  - {e.path}: {e.message}" for e in errors]
            message = "Configuration validation failed:\n" + "\n".join(error_msgs)
        else:
            self.errors = []
            message = str(errors)

        super().__init__(message)


class BuildError(DataikuIaCError):
    """Failed to build state from configuration"""
    pass
