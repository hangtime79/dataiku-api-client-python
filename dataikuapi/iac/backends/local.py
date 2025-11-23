"""
Local file-based state storage backend.

This module provides LocalFileBackend, a file-based state storage
implementation suitable for local development and single-user scenarios.
"""

import json
from pathlib import Path
import shutil

from dataikuapi.iac.backends.base import StateBackend
from dataikuapi.iac.models.state import State
from dataikuapi.iac.exceptions import (
    StateNotFoundError,
    StateCorruptedError,
    StateWriteError
)


class LocalFileBackend(StateBackend):
    """
    Local file-based state storage.

    Storage location: Configurable path (typically .dataiku/state/{environment}.state.json)

    Features:
        - Atomic writes (write to temp, then rename)
        - Automatic backups on save
        - JSON Schema validation (when available)
        - Directory creation if doesn't exist

    Example:
        >>> from pathlib import Path
        >>> backend = LocalFileBackend(Path(".dataiku/state/prod.state.json"))
        >>> state = State(environment="prod")
        >>> backend.save(state)
        >>> loaded_state = backend.load()
    """

    def __init__(self, state_file: Path):
        """
        Initialize local file backend.

        Args:
            state_file: Path to state file (will be created if doesn't exist)

        Note:
            Parent directory will be created automatically if it doesn't exist.
        """
        self.state_file = Path(state_file)
        # Create parent directory if it doesn't exist
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> State:
        """
        Load state from file.

        Returns:
            State object

        Raises:
            StateNotFoundError: If state file doesn't exist
            StateCorruptedError: If state file is invalid JSON or corrupted
        """
        if not self.exists():
            raise StateNotFoundError(f"State file not found: {self.state_file}")

        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)

            # TODO: Add JSON Schema validation here (Package 8)

            return State.from_dict(data)

        except json.JSONDecodeError as e:
            raise StateCorruptedError(f"Invalid JSON in state file: {e}")
        except KeyError as e:
            raise StateCorruptedError(f"Missing required field in state: {e}")
        except Exception as e:
            raise StateCorruptedError(f"Failed to parse state: {e}")

    def save(self, state: State) -> None:
        """
        Save state to file atomically.

        Uses atomic write pattern:
        1. Backup existing state if it exists
        2. Write to temporary file
        3. Rename temp file to target (atomic operation)

        Args:
            state: State to persist

        Raises:
            StateWriteError: If save operation fails
        """
        try:
            # Backup existing state if it exists
            if self.exists():
                self.backup(suffix=f"pre-serial-{state.serial}")

            # Write to temp file first (atomic write pattern)
            temp_file = self.state_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(state.to_dict(), f, indent=2)

            # Atomic rename - this is atomic on POSIX systems
            temp_file.rename(self.state_file)

        except Exception as e:
            # Clean up temp file if it exists
            temp_file = self.state_file.with_suffix('.tmp')
            if temp_file.exists():
                temp_file.unlink()
            raise StateWriteError(f"Failed to save state: {e}")

    def exists(self) -> bool:
        """
        Check if state file exists.

        Returns:
            True if state file exists, False otherwise
        """
        return self.state_file.exists()

    def delete(self) -> None:
        """
        Delete state file.

        Use with caution - this operation cannot be undone.
        Consider using backup() before deleting.

        Raises:
            StateNotFoundError: If state file doesn't exist
        """
        if not self.exists():
            raise StateNotFoundError(f"State file not found: {self.state_file}")

        self.state_file.unlink()

    def backup(self, suffix: str = "backup") -> Path:
        """
        Create backup of current state file.

        Backup filename format: {basename}.{suffix}.json

        Args:
            suffix: Backup identifier (default: "backup")
                   Common patterns:
                   - "backup" for general backups
                   - "pre-serial-{N}" for automatic backups before saves
                   - timestamp strings for point-in-time backups

        Returns:
            Path to backup file

        Raises:
            StateNotFoundError: If no state exists to backup

        Example:
            >>> backend = LocalFileBackend(Path("prod.state.json"))
            >>> backup_path = backend.backup(suffix="pre-apply")
            >>> print(backup_path)
            prod.state.pre-apply.json
        """
        if not self.exists():
            raise StateNotFoundError(f"No state to backup: {self.state_file}")

        # Generate backup filename
        backup_file = self.state_file.with_suffix(f'.{suffix}.json')

        # Copy state file to backup
        shutil.copy2(self.state_file, backup_file)

        return backup_file
