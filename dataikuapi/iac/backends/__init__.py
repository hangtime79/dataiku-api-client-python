"""
State backend implementations for Dataiku IaC.

This module provides various backends for persisting state:
- StateBackend: Abstract base class defining the interface
- LocalFileBackend: File-based storage for local development
"""

from dataikuapi.iac.backends.base import StateBackend
from dataikuapi.iac.backends.local import LocalFileBackend

__all__ = ['StateBackend', 'LocalFileBackend']
