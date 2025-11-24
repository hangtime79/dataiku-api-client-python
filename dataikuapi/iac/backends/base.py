"""
Abstract interface for state storage backends.

This module defines the StateBackend abstract base class that all
backend implementations must implement.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from dataikuapi.iac.models.state import State


class StateBackend(ABC):
    """
    Abstract interface for state storage backends.

    Implementations:
        - LocalFileBackend (Week 1)
        - S3Backend (Phase 1, Month 3)
        - GitBackend (future)

    All backends must provide:
        - load(): Read state from storage
        - save(): Write state to storage
        - exists(): Check if state exists
        - delete(): Remove state
        - backup(): Create backup copy
    """

    @abstractmethod
    def load(self) -> State:
        """
        Load state from backend.

        Returns:
            State object

        Raises:
            StateNotFoundError: If state doesn't exist
            StateCorruptedError: If state is invalid
        """
        pass

    @abstractmethod
    def save(self, state: State) -> None:
        """
        Save state to backend.

        Args:
            state: State to persist

        Raises:
            StateWriteError: If save fails
        """
        pass

    @abstractmethod
    def exists(self) -> bool:
        """
        Check if state exists in backend.

        Returns:
            True if state exists, False otherwise
        """
        pass

    @abstractmethod
    def delete(self) -> None:
        """
        Delete state from backend.

        Use with caution - this operation is typically irreversible.

        Raises:
            StateNotFoundError: If state doesn't exist
        """
        pass

    @abstractmethod
    def backup(self, suffix: str = "backup") -> Path:
        """
        Create backup of current state.

        Args:
            suffix: Backup file suffix/identifier

        Returns:
            Path to backup file

        Raises:
            StateNotFoundError: If no state exists to backup
        """
        pass
