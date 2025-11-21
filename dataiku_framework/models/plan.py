"""
Execution plan and result models

Represents planned changes and execution results.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from dataiku_framework.models.state import Diff
from dataiku_framework.config.schema import FrameworkConfig


class ExecutionStatus(Enum):
    """Status of an execution"""

    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"  # Some operations succeeded, some failed


@dataclass
class ResourceResult:
    """Result of operating on a single resource"""

    resource_type: str  # dataset, recipe, scenario
    name: str
    operation: str  # create, update, delete
    status: ExecutionStatus
    message: str = ""
    error: Optional[str] = None
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        """Export result to dictionary"""
        return {
            "resource_type": self.resource_type,
            "name": self.name,
            "operation": self.operation,
            "status": self.status.value,
            "message": self.message,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
        }

    def summary(self) -> str:
        """Human-readable summary"""
        status_emoji = {
            ExecutionStatus.SUCCESS: "✓",
            ExecutionStatus.FAILED: "✗",
            ExecutionStatus.CANCELLED: "○",
            ExecutionStatus.PARTIAL: "⚠",
        }
        emoji = status_emoji.get(self.status, "?")
        msg = f" - {self.message}" if self.message else ""
        return f"{emoji} {self.operation} {self.resource_type}: {self.name}{msg}"


@dataclass
class Plan:
    """
    Execution plan - preview of changes to be made.

    Similar to 'terraform plan' - shows what will change without executing.
    """

    config: FrameworkConfig
    diff: Diff
    created_at: datetime = field(default_factory=datetime.now)
    estimated_duration: Optional[float] = None  # seconds

    def has_changes(self) -> bool:
        """Check if plan has any changes"""
        return self.diff.has_changes()

    def summary(self) -> str:
        """Summary of planned changes"""
        if not self.has_changes():
            return "No changes - current state matches desired configuration"

        stats = self.diff.summary()
        total = stats["total"]
        return (
            f"Plan will make {total} change{'s' if total != 1 else ''}: "
            f"{stats['datasets']['create'] + stats['recipes']['create'] + stats['scenarios']['create']} create, "
            f"{stats['datasets']['update'] + stats['recipes']['update'] + stats['scenarios']['update']} update, "
            f"{stats['datasets']['delete'] + stats['recipes']['delete'] + stats['scenarios']['delete']} delete"
        )

    def to_markdown(self) -> str:
        """Format plan as markdown"""
        lines = [
            f"# Execution Plan\n",
            f"**Project:** {self.config.project.key}",
            f"**Created:** {self.created_at.isoformat()}\n",
        ]

        lines.append(self.diff.to_markdown())

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Export plan to dictionary"""
        return {
            "project_key": self.config.project.key,
            "created_at": self.created_at.isoformat(),
            "diff": self.diff.summary(),
            "estimated_duration": self.estimated_duration,
        }


@dataclass
class Result:
    """
    Execution result - outcome of applying changes.

    Similar to 'terraform apply' output - shows what actually happened.
    """

    status: ExecutionStatus
    project_key: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Detailed results
    results: List[ResourceResult] = field(default_factory=list)

    # Summary statistics
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0

    # Error information
    errors: List[str] = field(default_factory=list)

    def add_result(self, result: ResourceResult):
        """Add a resource result"""
        self.results.append(result)

        if result.status == ExecutionStatus.SUCCESS:
            self.success_count += 1
        elif result.status == ExecutionStatus.FAILED:
            self.failed_count += 1
            if result.error:
                self.errors.append(f"{result.name}: {result.error}")

    def finalize(self):
        """Finalize result after execution"""
        self.completed_at = datetime.now()
        self.duration_seconds = (
            self.completed_at - self.started_at
        ).total_seconds()

        # Determine overall status
        if self.failed_count == 0:
            self.status = ExecutionStatus.SUCCESS
        elif self.success_count == 0:
            self.status = ExecutionStatus.FAILED
        else:
            self.status = ExecutionStatus.PARTIAL

    def summary(self) -> str:
        """Summary of execution"""
        total = len(self.results)
        return (
            f"Execution {self.status.value}: "
            f"{self.success_count}/{total} succeeded, "
            f"{self.failed_count}/{total} failed "
            f"({self.duration_seconds:.1f}s)"
        )

    def to_markdown(self) -> str:
        """Format result as markdown"""
        lines = [
            f"# Execution Result\n",
            f"**Project:** {self.project_key}",
            f"**Status:** {self.status.value.upper()}",
            f"**Duration:** {self.duration_seconds:.2f}s\n",
        ]

        # Summary
        lines.append("## Summary\n")
        lines.append(
            f"- **Success:** {self.success_count}/{len(self.results)}"
        )
        lines.append(f"- **Failed:** {self.failed_count}/{len(self.results)}")
        if self.skipped_count > 0:
            lines.append(f"- **Skipped:** {self.skipped_count}/{len(self.results)}")
        lines.append("")

        # Detailed results
        if self.results:
            lines.append("## Details\n")
            for result in self.results:
                lines.append(result.summary())
                if result.error:
                    lines.append(f"  Error: {result.error}")
            lines.append("")

        # Errors summary
        if self.errors:
            lines.append("## Errors\n")
            for error in self.errors:
                lines.append(f"- {error}")
            lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Export result to dictionary"""
        return {
            "status": self.status.value,
            "project_key": self.project_key,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "duration_seconds": self.duration_seconds,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "results": [r.to_dict() for r in self.results],
            "errors": self.errors,
        }
