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
