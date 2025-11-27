# Dataiku IaC - Wave 4 Planning: Apply Execution

**Date:** 2025-11-27
**Status:** Planning Document
**Version:** 0.1.0

---

## Executive Summary

Wave 4 implements the **apply execution engine** - the critical component that transforms execution plans into real Dataiku infrastructure changes. This completes the core IaC workflow: parse → validate → plan → **apply**.

With Wave 4, users will be able to:
- Execute plans to create/update/delete resources in Dataiku
- Resume interrupted operations from checkpoints
- Rollback on failures to maintain consistency
- Track progress through multi-step executions
- Use a production-ready `dataiku-iac apply` command

**Complexity Estimate:** Similar to Wave 3 in scope (~3,000 lines), but higher technical risk due to:
- Real Dataiku API operations (can't be fully mocked)
- Checkpoint/rollback state management
- Error recovery mechanisms
- Integration with existing API client patterns

---

## Wave Context

### Completed Waves

| Wave | Focus | Status | Key Deliverables |
|------|-------|--------|------------------|
| **Wave 1** | State Management | ✅ Complete | State model, sync engine, diff engine, backends |
| **Wave 3** | Plan Generation | ✅ Complete | Config parser, validator, plan generator, CLI plan |

### Wave 4 Dependencies

**Builds on:**
- Wave 1: `State`, `Resource`, `DiffEngine`, `StateManager`, resource syncs
- Wave 3: `ExecutionPlan`, `PlannedAction`, `ActionType`, `ConfigParser`

**Provides foundation for:**
- Wave 5: State refresh, import, drift detection
- Wave 6+: CI/CD integration, Govern workflows, testing framework

---

## Architecture Overview

### Apply Engine Flow

```
ExecutionPlan
    ↓
ApplyEngine.apply(plan)
    ↓
├── Initialize checkpoint
├── For each action in plan:
│   ├── Check dependencies satisfied
│   ├── Execute via ResourceExecutor
│   │   ├── ProjectExecutor
│   │   ├── DatasetExecutor
│   │   └── RecipeExecutor
│   ├── Update checkpoint
│   └── Report progress
├── On success: Finalize state
└── On failure: Rollback via checkpoint

Result: ApplyResult with:
- actions_completed
- actions_failed
- final_state
- rollback_info (if applicable)
```

### Key Design Decisions

#### 1. Checkpoint Strategy: Incremental State Updates

**Decision:** Update state file after each successful action, not just at the end.

**Rationale:**
- Enables resume from any point
- State file is always consistent (reflects actual Dataiku state)
- Easier to debug (can see exactly what was created)
- Matches Terraform's behavior

**Implementation:**
```python
# After each successful action:
1. Execute action in Dataiku
2. Sync resource back from Dataiku (verify creation)
3. Update state with actual resource
4. Save state to checkpoint file
5. Continue to next action
```

#### 2. Rollback Strategy: Best-Effort Cleanup

**Decision:** Attempt to delete created resources on failure, but don't guarantee atomicity.

**Rationale:**
- Dataiku doesn't support transactions
- Full atomicity is impossible (can't rollback a project creation if dataset creation fails)
- Best-effort rollback is better than nothing
- Clear error messages help manual cleanup

**Implementation:**
```python
# On failure:
1. Log the failure point
2. Attempt to delete resources created in this apply (reverse order)
3. Restore state to pre-apply checkpoint
4. Report what was cleaned up vs what requires manual intervention
```

#### 3. Dry-Run Mode: Plan Validation

**Decision:** Dry-run is just `plan` - no separate mode in apply.

**Rationale:**
- `plan` command already shows what will happen
- Dry-run in `apply` would duplicate functionality
- Simpler mental model (plan = preview, apply = execute)

#### 4. Progress Reporting: Callback-Based

**Decision:** Use callback functions for progress updates, not just logging.

**Rationale:**
- Enables rich CLI progress bars
- Allows integration with external systems (webhooks, Govern)
- Testable without parsing logs
- Non-blocking (async-friendly)

---

## Package Breakdown

### Package 1: Apply Engine Core

**Purpose:** Orchestrate plan execution with checkpoint management

**Location:** `dataikuapi/iac/apply/engine.py`

**Classes:**

```python
class ApplyEngine:
    """
    Execute plans against Dataiku.

    Manages:
    - Action execution orchestration
    - Checkpoint creation/restoration
    - Rollback on failure
    - Progress reporting
    """

    def __init__(
        self,
        client: DSSClient,
        state_manager: StateManager,
        progress_callback: Optional[Callable] = None
    ):
        """
        Args:
            client: Dataiku API client
            state_manager: State manager for checkpoint operations
            progress_callback: Optional callback(action, status, message)
        """

    def apply(
        self,
        plan: ExecutionPlan,
        auto_approve: bool = False
    ) -> ApplyResult:
        """
        Execute plan.

        Args:
            plan: Execution plan to apply
            auto_approve: If False, prompt user for confirmation

        Returns:
            ApplyResult with completion status

        Raises:
            ApplyError: If apply fails
        """

    def resume(self, checkpoint_file: str) -> ApplyResult:
        """
        Resume interrupted apply from checkpoint.

        Args:
            checkpoint_file: Path to checkpoint file

        Returns:
            ApplyResult with completion status
        """

    def rollback(self, actions: List[PlannedAction]) -> RollbackResult:
        """
        Rollback completed actions (best-effort).

        Args:
            actions: List of actions to reverse

        Returns:
            RollbackResult with cleanup status
        """
```

**Data Models:**

```python
@dataclass
class ApplyResult:
    """Result of apply operation"""
    success: bool
    actions_completed: List[PlannedAction]
    actions_failed: List[Tuple[PlannedAction, Exception]]
    final_state: State
    rollback_performed: bool = False
    rollback_result: Optional[RollbackResult] = None
    duration_seconds: float = 0.0

    def summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""

@dataclass
class RollbackResult:
    """Result of rollback operation"""
    success: bool
    resources_deleted: List[str]
    resources_failed: List[Tuple[str, Exception]]
    manual_cleanup_required: List[str]

@dataclass
class Checkpoint:
    """Checkpoint state for resume capability"""
    plan: ExecutionPlan
    completed_actions: List[PlannedAction]
    current_state: State
    timestamp: datetime
    environment: str
```

**Error Handling:**

```python
class ApplyError(DataikuIaCError):
    """Base error for apply operations"""

class ExecutionError(ApplyError):
    """Error executing specific action"""
    def __init__(self, action: PlannedAction, cause: Exception):
        self.action = action
        self.cause = cause

class RollbackError(ApplyError):
    """Error during rollback"""

class CheckpointError(ApplyError):
    """Error with checkpoint operations"""
```

**Testing Approach:**

```python
# tests/iac/test_apply_engine.py

class TestApplyEngine:
    def test_apply_empty_plan(self, mock_client):
        """Empty plan completes successfully"""

    def test_apply_creates_resources(self, mock_client):
        """Create actions execute correctly"""

    def test_apply_updates_resources(self, mock_client):
        """Update actions execute correctly"""

    def test_apply_deletes_resources(self, mock_client):
        """Delete actions execute correctly"""

    def test_apply_updates_state_incrementally(self, mock_client):
        """State updated after each action"""

    def test_apply_failure_triggers_rollback(self, mock_client):
        """Failure in middle triggers rollback"""

    def test_resume_from_checkpoint(self, mock_client, tmp_path):
        """Can resume interrupted apply"""

    def test_rollback_reverses_creates(self, mock_client):
        """Rollback deletes created resources"""

    def test_progress_callback_invoked(self, mock_client):
        """Progress callback called for each action"""
```

**Coverage Target:** 90%+

---

### Package 2: Resource Executors

**Purpose:** Execute create/update/delete operations for each resource type

**Location:** `dataikuapi/iac/apply/executors/`

**Structure:**

```
dataikuapi/iac/apply/executors/
├── __init__.py
├── base.py          # Abstract ResourceExecutor
├── project.py       # ProjectExecutor
├── dataset.py       # DatasetExecutor
└── recipe.py        # RecipeExecutor
```

**Base Executor:**

```python
# base.py

class ResourceExecutor(ABC):
    """
    Abstract base for resource executors.

    Each resource type implements create/update/delete logic.
    """

    def __init__(self, client: DSSClient):
        self.client = client

    @abstractmethod
    def create(self, action: PlannedAction) -> Resource:
        """
        Create resource in Dataiku.

        Args:
            action: PlannedAction with CREATE action_type

        Returns:
            Resource representing created resource (synced from Dataiku)

        Raises:
            ExecutionError: If creation fails
        """

    @abstractmethod
    def update(self, action: PlannedAction) -> Resource:
        """
        Update resource in Dataiku.

        Args:
            action: PlannedAction with UPDATE action_type

        Returns:
            Resource representing updated resource (synced from Dataiku)

        Raises:
            ExecutionError: If update fails
        """

    @abstractmethod
    def delete(self, action: PlannedAction) -> None:
        """
        Delete resource from Dataiku.

        Args:
            action: PlannedAction with DELETE action_type

        Raises:
            ExecutionError: If deletion fails
        """

    @property
    @abstractmethod
    def resource_type(self) -> str:
        """Resource type this executor handles"""
```

**Project Executor:**

```python
# project.py

class ProjectExecutor(ResourceExecutor):
    """Execute project operations"""

    @property
    def resource_type(self) -> str:
        return "project"

    def create(self, action: PlannedAction) -> Resource:
        """
        Create project in Dataiku.

        Steps:
        1. Extract attributes from action.diff.after
        2. Call client.create_project(project_key, name, ...)
        3. Get project and update settings
        4. Sync back from Dataiku to get actual state
        5. Return Resource
        """
        project_key = action.diff.after["projectKey"]
        name = action.diff.after.get("name", project_key)
        description = action.diff.after.get("description", "")

        try:
            # Create project
            project = self.client.create_project(
                project_key=project_key,
                name=name,
                owner=None,  # Use current user
                description=description
            )

            # Update additional settings if needed
            settings = project.get_settings()
            settings.settings["shortDesc"] = action.diff.after.get("shortDesc", "")
            settings.settings["tags"] = action.diff.after.get("tags", [])
            settings.save()

            # Sync back to get actual state
            sync = ProjectSync(self.client)
            return sync.fetch(action.resource_id)

        except Exception as e:
            raise ExecutionError(action, e)

    def update(self, action: PlannedAction) -> Resource:
        """Update project settings"""
        # Similar pattern: get settings, apply changes, save, sync back

    def delete(self, action: PlannedAction) -> None:
        """Delete project"""
        parts = action.resource_id.split('.')
        project_key = parts[1]

        try:
            project = self.client.get_project(project_key)
            project.delete(clear_managed_datasets=True)
        except Exception as e:
            raise ExecutionError(action, e)
```

**Dataset Executor:**

```python
# dataset.py

class DatasetExecutor(ResourceExecutor):
    """Execute dataset operations"""

    @property
    def resource_type(self) -> str:
        return "dataset"

    def create(self, action: PlannedAction) -> Resource:
        """
        Create dataset in Dataiku.

        Handles:
        - Managed datasets (all format types)
        - SQL datasets
        - Filesystem datasets
        - Upload datasets
        """
        parts = action.resource_id.split('.')
        project_key = parts[1]
        dataset_name = parts[2]

        attributes = action.diff.after
        dataset_type = attributes.get("type")

        try:
            project = self.client.get_project(project_key)

            if dataset_type == "managed":
                # Create managed dataset
                format_type = attributes.get("format_type", "parquet")
                dataset = project.create_managed_dataset(
                    dataset_name=dataset_name,
                    format_type=format_type
                )

            elif dataset_type == "sql":
                # Create SQL dataset
                connection = attributes.get("connection")
                params = attributes.get("params", {})
                dataset = project.create_sql_table_dataset(
                    dataset_name=dataset_name,
                    connection=connection,
                    table=params.get("table"),
                    schema=params.get("schema")
                )

            # Apply additional settings
            settings = dataset.get_settings()
            # Update description, tags, etc.
            if "description" in attributes:
                settings.settings["description"] = attributes["description"]
            if "tags" in attributes:
                settings.settings["tags"] = attributes["tags"]
            settings.save()

            # Sync back
            sync = DatasetSync(self.client)
            return sync.fetch(action.resource_id)

        except Exception as e:
            raise ExecutionError(action, e)

    def update(self, action: PlannedAction) -> Resource:
        """Update dataset settings"""
        # Get dataset, apply changes from diff, save, sync back

    def delete(self, action: PlannedAction) -> None:
        """Delete dataset"""
        parts = action.resource_id.split('.')
        project_key = parts[1]
        dataset_name = parts[2]

        try:
            project = self.client.get_project(project_key)
            dataset = project.get_dataset(dataset_name)
            dataset.delete(drop_data=True)
        except Exception as e:
            raise ExecutionError(action, e)
```

**Recipe Executor:**

```python
# recipe.py

class RecipeExecutor(ResourceExecutor):
    """Execute recipe operations"""

    @property
    def resource_type(self) -> str:
        return "recipe"

    def create(self, action: PlannedAction) -> Resource:
        """
        Create recipe in Dataiku.

        Handles:
        - Python recipes
        - SQL recipes
        - Visual recipes (future)
        """
        parts = action.resource_id.split('.')
        project_key = parts[1]
        recipe_name = parts[2]

        attributes = action.diff.after
        recipe_type = attributes.get("type")

        try:
            project = self.client.get_project(project_key)

            # Get input/output refs
            inputs = self._build_input_refs(attributes.get("inputs", []), project_key)
            outputs = self._build_output_refs(attributes.get("outputs", []), project_key)

            if recipe_type == "python":
                # Create Python recipe
                recipe = project.create_recipe(
                    recipe_type="python",
                    name=recipe_name,
                    inputs=inputs,
                    outputs=outputs
                )

                # Set code
                if "code" in attributes:
                    recipe.get_settings().set_code(attributes["code"])
                    recipe.get_settings().save()

            elif recipe_type == "sql":
                # Create SQL recipe
                recipe = project.create_recipe(
                    recipe_type="sql_query",
                    name=recipe_name,
                    inputs=inputs,
                    outputs=outputs
                )

                # Set SQL code
                if "sql" in attributes:
                    recipe.get_settings().set_code(attributes["sql"])
                    recipe.get_settings().save()

            # Sync back
            sync = RecipeSync(self.client)
            return sync.fetch(action.resource_id)

        except Exception as e:
            raise ExecutionError(action, e)

    def _build_input_refs(self, inputs: List[str], project_key: str) -> Dict:
        """Convert input names to Dataiku input refs"""
        return {
            "main": [{"ref": inp, "projectKey": project_key} for inp in inputs]
        }

    def _build_output_refs(self, outputs: List[str], project_key: str) -> Dict:
        """Convert output names to Dataiku output refs"""
        return {
            "main": [{"ref": out, "projectKey": project_key} for out in outputs]
        }

    def update(self, action: PlannedAction) -> Resource:
        """Update recipe settings/code"""

    def delete(self, action: PlannedAction) -> None:
        """Delete recipe"""
```

**Executor Registry:**

```python
# __init__.py

class ExecutorRegistry:
    """Registry of resource executors"""

    def __init__(self, client: DSSClient):
        self.client = client
        self._executors = {
            "project": ProjectExecutor(client),
            "dataset": DatasetExecutor(client),
            "recipe": RecipeExecutor(client),
        }

    def get_executor(self, resource_type: str) -> ResourceExecutor:
        """Get executor for resource type"""
        if resource_type not in self._executors:
            raise ValueError(f"No executor for resource type: {resource_type}")
        return self._executors[resource_type]

    def execute_action(self, action: PlannedAction) -> Optional[Resource]:
        """Execute action using appropriate executor"""
        executor = self.get_executor(action.resource_type)

        if action.action_type == ActionType.CREATE:
            return executor.create(action)
        elif action.action_type == ActionType.UPDATE:
            return executor.update(action)
        elif action.action_type == ActionType.DELETE:
            executor.delete(action)
            return None
        elif action.action_type == ActionType.NO_CHANGE:
            return None  # Nothing to do
        else:
            raise ValueError(f"Unknown action type: {action.action_type}")
```

**Testing Approach:**

```python
# tests/iac/test_executors.py

class TestProjectExecutor:
    def test_create_project(self, mock_client):
        """Create project with all attributes"""

    def test_update_project_description(self, mock_client):
        """Update project description"""

    def test_delete_project(self, mock_client):
        """Delete project"""

    def test_create_handles_api_error(self, mock_client):
        """Create raises ExecutionError on API failure"""

class TestDatasetExecutor:
    def test_create_managed_dataset_parquet(self, mock_client):
        """Create parquet managed dataset"""

    def test_create_managed_dataset_csv(self, mock_client):
        """Create CSV managed dataset"""

    def test_create_sql_dataset(self, mock_client):
        """Create SQL dataset with connection"""

    def test_update_dataset_settings(self, mock_client):
        """Update dataset description and tags"""

    def test_delete_dataset(self, mock_client):
        """Delete dataset with data"""

class TestRecipeExecutor:
    def test_create_python_recipe(self, mock_client):
        """Create Python recipe with code"""

    def test_create_sql_recipe(self, mock_client):
        """Create SQL recipe with query"""

    def test_update_recipe_code(self, mock_client):
        """Update recipe code"""

    def test_delete_recipe(self, mock_client):
        """Delete recipe"""

    def test_create_validates_inputs_exist(self, mock_client):
        """Create fails if input datasets don't exist"""
```

**Coverage Target:** 85%+ (harder to test due to Dataiku API dependencies)

---

### Package 3: Checkpoint System

**Purpose:** Save/restore apply state for resume capability

**Location:** `dataikuapi/iac/apply/checkpoint.py`

**Classes:**

```python
class CheckpointManager:
    """
    Manage apply checkpoints.

    Checkpoints enable resume from interruption.
    """

    def __init__(self, checkpoint_dir: str = ".dataiku-iac/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def create_checkpoint(
        self,
        plan: ExecutionPlan,
        completed_actions: List[PlannedAction],
        current_state: State,
        environment: str
    ) -> str:
        """
        Create checkpoint file.

        Args:
            plan: Original execution plan
            completed_actions: Actions completed so far
            current_state: Current state (with completed resources)
            environment: Environment name

        Returns:
            Path to checkpoint file
        """
        checkpoint = Checkpoint(
            plan=plan,
            completed_actions=completed_actions,
            current_state=current_state,
            timestamp=datetime.utcnow(),
            environment=environment
        )

        # Generate filename: apply-{env}-{timestamp}.checkpoint
        timestamp_str = checkpoint.timestamp.strftime("%Y%m%d-%H%M%S")
        filename = f"apply-{environment}-{timestamp_str}.checkpoint"
        filepath = self.checkpoint_dir / filename

        # Serialize to JSON
        data = {
            "version": "1.0",
            "checkpoint": {
                "plan": self._serialize_plan(checkpoint.plan),
                "completed_actions": [a.resource_id for a in checkpoint.completed_actions],
                "current_state": checkpoint.current_state.to_dict(),
                "timestamp": checkpoint.timestamp.isoformat(),
                "environment": checkpoint.environment
            }
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        return str(filepath)

    def load_checkpoint(self, checkpoint_file: str) -> Checkpoint:
        """
        Load checkpoint from file.

        Args:
            checkpoint_file: Path to checkpoint file

        Returns:
            Checkpoint object

        Raises:
            CheckpointError: If file doesn't exist or is invalid
        """
        filepath = Path(checkpoint_file)
        if not filepath.exists():
            raise CheckpointError(f"Checkpoint file not found: {checkpoint_file}")

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Deserialize
            checkpoint_data = data["checkpoint"]
            return Checkpoint(
                plan=self._deserialize_plan(checkpoint_data["plan"]),
                completed_actions=self._deserialize_actions(checkpoint_data["completed_actions"]),
                current_state=State.from_dict(checkpoint_data["current_state"]),
                timestamp=datetime.fromisoformat(checkpoint_data["timestamp"]),
                environment=checkpoint_data["environment"]
            )

        except Exception as e:
            raise CheckpointError(f"Failed to load checkpoint: {e}")

    def get_pending_actions(self, checkpoint: Checkpoint) -> List[PlannedAction]:
        """
        Get actions that haven't been completed yet.

        Args:
            checkpoint: Checkpoint with completed actions

        Returns:
            List of pending PlannedAction objects
        """
        completed_ids = {a.resource_id for a in checkpoint.completed_actions}
        return [
            action for action in checkpoint.plan.actions
            if action.resource_id not in completed_ids
        ]

    def cleanup_old_checkpoints(self, keep_count: int = 5):
        """
        Remove old checkpoint files, keeping most recent N.

        Args:
            keep_count: Number of recent checkpoints to keep
        """
        checkpoints = sorted(
            self.checkpoint_dir.glob("apply-*.checkpoint"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        for checkpoint_file in checkpoints[keep_count:]:
            checkpoint_file.unlink()
```

**Testing Approach:**

```python
# tests/iac/test_checkpoint.py

class TestCheckpointManager:
    def test_create_checkpoint(self, tmp_path):
        """Create checkpoint file with all data"""

    def test_load_checkpoint(self, tmp_path):
        """Load checkpoint and deserialize correctly"""

    def test_get_pending_actions(self, tmp_path):
        """Get actions not yet completed"""

    def test_cleanup_old_checkpoints(self, tmp_path):
        """Keep only N most recent checkpoints"""

    def test_load_missing_checkpoint_raises(self, tmp_path):
        """Loading missing checkpoint raises CheckpointError"""

    def test_roundtrip_serialization(self, tmp_path):
        """Create → save → load → get same data"""
```

**Coverage Target:** 95%+

---

### Package 4: Rollback Mechanism

**Purpose:** Cleanup resources on apply failure

**Location:** `dataikuapi/iac/apply/rollback.py`

**Classes:**

```python
class RollbackManager:
    """
    Rollback apply operations.

    Best-effort cleanup of created resources on failure.
    """

    def __init__(self, client: DSSClient):
        self.client = client
        self.executor_registry = ExecutorRegistry(client)

    def rollback(
        self,
        completed_actions: List[PlannedAction],
        pre_apply_state: State
    ) -> RollbackResult:
        """
        Rollback completed actions.

        Strategy:
        1. Identify resources created in this apply (not in pre_apply_state)
        2. Delete them in reverse dependency order
        3. Track successes/failures
        4. Return result with manual cleanup list

        Args:
            completed_actions: Actions that were completed before failure
            pre_apply_state: State before apply started

        Returns:
            RollbackResult with cleanup status
        """
        resources_deleted = []
        resources_failed = []
        manual_cleanup = []

        # Identify new resources (created in this apply)
        new_resource_ids = {
            action.resource_id
            for action in completed_actions
            if action.action_type == ActionType.CREATE
        }

        # Order deletions in reverse dependency order
        delete_actions = self._build_delete_actions(
            new_resource_ids,
            completed_actions
        )

        # Execute deletions
        for action in delete_actions:
            try:
                executor = self.executor_registry.get_executor(action.resource_type)
                executor.delete(action)
                resources_deleted.append(action.resource_id)
            except Exception as e:
                resources_failed.append((action.resource_id, e))
                manual_cleanup.append(action.resource_id)

        success = len(resources_failed) == 0

        return RollbackResult(
            success=success,
            resources_deleted=resources_deleted,
            resources_failed=resources_failed,
            manual_cleanup_required=manual_cleanup
        )

    def _build_delete_actions(
        self,
        resource_ids: Set[str],
        completed_actions: List[PlannedAction]
    ) -> List[PlannedAction]:
        """
        Build delete actions in reverse dependency order.

        Args:
            resource_ids: Set of resource IDs to delete
            completed_actions: Completed actions (for dependency info)

        Returns:
            List of delete PlannedAction objects in reverse order
        """
        # Build delete actions
        delete_actions = []
        action_map = {a.resource_id: a for a in completed_actions}

        for resource_id in resource_ids:
            original_action = action_map.get(resource_id)
            if not original_action:
                continue

            # Create delete action
            delete_action = PlannedAction(
                action_type=ActionType.DELETE,
                resource_id=resource_id,
                resource_type=original_action.resource_type,
                diff=original_action.diff,  # Keep diff for context
                dependencies=original_action.dependencies
            )
            delete_actions.append(delete_action)

        # Order in reverse (recipes before datasets before projects)
        # Use PlanGenerator's topological sort with reverse=True
        from ..planner.engine import PlanGenerator
        planner = PlanGenerator()
        return planner._topological_sort(delete_actions, reverse=True)
```

**Testing Approach:**

```python
# tests/iac/test_rollback.py

class TestRollbackManager:
    def test_rollback_created_resources(self, mock_client):
        """Rollback deletes created resources"""

    def test_rollback_preserves_existing_resources(self, mock_client):
        """Rollback doesn't delete pre-existing resources"""

    def test_rollback_reverse_dependency_order(self, mock_client):
        """Rollback deletes recipes before datasets before projects"""

    def test_rollback_partial_failure(self, mock_client):
        """Rollback continues on individual failures"""

    def test_rollback_returns_manual_cleanup_list(self, mock_client):
        """Rollback reports resources requiring manual cleanup"""
```

**Coverage Target:** 85%+

---

### Package 5: Progress Reporting

**Purpose:** Track and report apply progress

**Location:** `dataikuapi/iac/apply/progress.py`

**Classes:**

```python
@dataclass
class ProgressEvent:
    """Single progress event"""
    action: PlannedAction
    status: str  # "started", "completed", "failed", "skipped"
    message: str
    timestamp: datetime
    duration_ms: Optional[int] = None
    error: Optional[Exception] = None


class ProgressReporter:
    """
    Track and report apply progress.

    Supports multiple output formats:
    - Console (default)
    - JSON (for automation)
    - Callback (for custom handling)
    """

    def __init__(
        self,
        output_format: str = "console",
        callback: Optional[Callable[[ProgressEvent], None]] = None,
        verbose: bool = False
    ):
        self.output_format = output_format
        self.callback = callback
        self.verbose = verbose
        self.events = []

    def report(
        self,
        action: PlannedAction,
        status: str,
        message: str = "",
        error: Optional[Exception] = None,
        duration_ms: Optional[int] = None
    ):
        """
        Report progress event.

        Args:
            action: Action being reported on
            status: "started", "completed", "failed", "skipped"
            message: Optional message
            error: Optional exception if failed
            duration_ms: Optional duration in milliseconds
        """
        event = ProgressEvent(
            action=action,
            status=status,
            message=message,
            timestamp=datetime.utcnow(),
            duration_ms=duration_ms,
            error=error
        )

        self.events.append(event)

        # Output based on format
        if self.output_format == "console":
            self._print_console(event)
        elif self.output_format == "json":
            self._print_json(event)

        # Call callback if provided
        if self.callback:
            self.callback(event)

    def _print_console(self, event: ProgressEvent):
        """Print to console with colors"""
        symbol = {
            "started": "⏳",
            "completed": "✓",
            "failed": "✗",
            "skipped": "○"
        }.get(event.status, "?")

        color_code = {
            "started": "\033[93m",  # Yellow
            "completed": "\033[92m",  # Green
            "failed": "\033[91m",  # Red
            "skipped": "\033[90m"  # Gray
        }.get(event.status, "")

        reset_code = "\033[0m"

        action_str = str(event.action)
        message = f" - {event.message}" if event.message else ""
        duration = f" ({event.duration_ms}ms)" if event.duration_ms else ""

        print(f"{color_code}{symbol} {action_str}{message}{duration}{reset_code}")

        if event.error and self.verbose:
            print(f"  Error: {event.error}")

    def _print_json(self, event: ProgressEvent):
        """Print JSON format"""
        data = {
            "resource_id": event.action.resource_id,
            "action_type": event.action.action_type.value,
            "status": event.status,
            "timestamp": event.timestamp.isoformat(),
            "message": event.message,
            "duration_ms": event.duration_ms,
            "error": str(event.error) if event.error else None
        }
        print(json.dumps(data))

    def get_summary(self) -> Dict[str, int]:
        """
        Get summary statistics.

        Returns:
            Dict with counts by status
        """
        summary = {
            "started": 0,
            "completed": 0,
            "failed": 0,
            "skipped": 0
        }

        for event in self.events:
            if event.status in summary:
                summary[event.status] += 1

        return summary
```

**Testing Approach:**

```python
# tests/iac/test_progress.py

class TestProgressReporter:
    def test_report_started(self):
        """Report started event"""

    def test_report_completed(self):
        """Report completed event"""

    def test_report_failed(self):
        """Report failed event with error"""

    def test_console_output(self, capsys):
        """Console output has correct format"""

    def test_json_output(self, capsys):
        """JSON output is valid"""

    def test_callback_invoked(self):
        """Callback called for each event"""

    def test_get_summary(self):
        """Summary counts events correctly"""
```

**Coverage Target:** 95%+

---

### Package 6: CLI Integration

**Purpose:** `dataiku-iac apply` command

**Location:** `dataikuapi/iac/cli/apply.py`

**CLI Design:**

```python
"""
CLI apply command for Dataiku IaC.

Usage:
    python -m dataikuapi.iac.cli.apply [OPTIONS]

Options:
    -c, --config FILE          Config file or directory (required)
    -e, --environment ENV      Environment name (required)
    --state-file FILE          Custom state file path
    --auto-approve             Skip confirmation prompt
    --resume CHECKPOINT        Resume from checkpoint file
    --no-rollback              Don't rollback on failure
    --output FORMAT            Output format: console, json (default: console)
    --checkpoint-dir DIR       Checkpoint directory (default: .dataiku-iac/checkpoints)
    -v, --verbose              Verbose output
    -h, --help                 Show help
"""

def main():
    """Apply command main entry point"""

    parser = argparse.ArgumentParser(
        description="Apply Dataiku infrastructure changes",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Arguments
    parser.add_argument("-c", "--config", required=True, help="Config file or directory")
    parser.add_argument("-e", "--environment", required=True, help="Environment name")
    parser.add_argument("--state-file", help="Custom state file path")
    parser.add_argument("--auto-approve", action="store_true", help="Skip confirmation")
    parser.add_argument("--resume", help="Resume from checkpoint file")
    parser.add_argument("--no-rollback", action="store_true", help="Don't rollback on failure")
    parser.add_argument("--output", choices=["console", "json"], default="console", help="Output format")
    parser.add_argument("--checkpoint-dir", default=".dataiku-iac/checkpoints", help="Checkpoint directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    try:
        # Initialize Dataiku client
        client = get_client()

        # Load state manager
        state_file = args.state_file or f"dataiku-{args.environment}.state.json"
        state_manager = StateManager(backend=LocalFileBackend(state_file))

        # Initialize apply engine
        progress_reporter = ProgressReporter(
            output_format=args.output,
            verbose=args.verbose
        )

        apply_engine = ApplyEngine(
            client=client,
            state_manager=state_manager,
            progress_callback=progress_reporter.report
        )

        if args.resume:
            # Resume from checkpoint
            print(f"Resuming from checkpoint: {args.resume}\n")
            result = apply_engine.resume(args.resume)

        else:
            # Normal apply flow
            # 1. Parse and validate config
            parser = ConfigParser()
            config = parser.parse_file(args.config) if Path(args.config).is_file() \
                else parser.parse_directory(args.config)

            validator = ConfigValidator()
            validator.validate(config)

            # 2. Build desired state
            builder = DesiredStateBuilder(environment=args.environment)
            desired_state = builder.build(config)

            # 3. Load current state
            current_state = state_manager.load_state()

            # 4. Generate plan
            planner = PlanGenerator()
            plan = planner.generate_plan(current_state, desired_state)

            # 5. Show plan
            formatter = PlanFormatter(color=(args.output == "console"))
            formatter.format(plan)

            # 6. Confirm
            if not args.auto_approve and plan.has_changes():
                response = input("\nDo you want to apply these changes? (yes/no): ")
                if response.lower() not in ["yes", "y"]:
                    print("Apply cancelled.")
                    return 0

            # 7. Apply
            print("\nApplying changes...\n")
            result = apply_engine.apply(
                plan=plan,
                auto_approve=True  # Already confirmed above
            )

        # Report results
        if result.success:
            print(f"\n✓ Apply completed successfully!")
            print(f"  - Actions completed: {len(result.actions_completed)}")
            print(f"  - Duration: {result.duration_seconds:.2f}s")
            return 0
        else:
            print(f"\n✗ Apply failed!")
            print(f"  - Actions completed: {len(result.actions_completed)}")
            print(f"  - Actions failed: {len(result.actions_failed)}")

            if result.rollback_performed:
                print(f"\nRollback performed:")
                print(f"  - Resources deleted: {len(result.rollback_result.resources_deleted)}")
                if result.rollback_result.manual_cleanup_required:
                    print(f"\n⚠ Manual cleanup required for:")
                    for resource_id in result.rollback_result.manual_cleanup_required:
                        print(f"  - {resource_id}")

            return 1

    except ConfigValidationError as e:
        print(f"✗ Configuration validation failed:")
        print(e)
        return 1

    except Exception as e:
        print(f"✗ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def get_client() -> DSSClient:
    """Get Dataiku client from environment"""
    # Read from DATAIKU_DSS_URL and DATAIKU_API_KEY env vars
    # Or from config file
    dss_url = os.getenv("DATAIKU_DSS_URL")
    api_key = os.getenv("DATAIKU_API_KEY")

    if not dss_url or not api_key:
        raise ValueError(
            "DATAIKU_DSS_URL and DATAIKU_API_KEY environment variables required"
        )

    return DSSClient(dss_url, api_key)
```

**Integration Tests:**

```python
# tests/iac/test_integration_apply.py

class TestApplyIntegration:
    """End-to-end apply workflow tests"""

    def test_apply_creates_project(self, mock_client, tmp_path):
        """Apply creates project from config"""

    def test_apply_updates_existing_resource(self, mock_client, tmp_path):
        """Apply updates existing resource"""

    def test_apply_deletes_removed_resource(self, mock_client, tmp_path):
        """Apply deletes resource not in config"""

    def test_apply_creates_checkpoint(self, mock_client, tmp_path):
        """Apply creates checkpoint file"""

    def test_resume_completes_partial_apply(self, mock_client, tmp_path):
        """Resume completes interrupted apply"""

    def test_apply_rollback_on_failure(self, mock_client, tmp_path):
        """Apply rolls back on failure"""

    def test_cli_apply_command(self, mock_client, tmp_path):
        """CLI apply command works end-to-end"""
```

**Coverage Target:** 75%+ (CLI harder to test)

---

## Integration Points

### With Wave 1 (State Management)

**Uses:**
- `State` model to track current/desired state
- `StateManager` for checkpoint operations
- `ResourceSync` classes to verify created resources
- `DiffEngine` via `PlanGenerator` (Wave 3)

**Integration:**
```python
# In ApplyEngine.apply():
# 1. Get current state
current_state = self.state_manager.load_state()

# 2. After each action, sync resource back
sync = self.sync_registry.get_sync(action.resource_type)
actual_resource = sync.fetch(action.resource_id)

# 3. Update state
current_state.add_resource(actual_resource)

# 4. Save checkpoint
self.state_manager.save_state(current_state)
```

### With Wave 3 (Plan Generation)

**Uses:**
- `ExecutionPlan` as input to apply
- `PlannedAction` for each operation
- `ActionType` enum for action routing

**Integration:**
```python
# In ApplyEngine.apply():
for action in plan.actions:
    executor = self.executor_registry.get_executor(action.resource_type)

    if action.action_type == ActionType.CREATE:
        resource = executor.create(action)
    elif action.action_type == ActionType.UPDATE:
        resource = executor.update(action)
    # etc.
```

### With Existing API Client

**Uses:**
- `DSSClient` for all Dataiku operations
- `DSSProject.create_dataset()`, `create_recipe()`, etc.
- Settings pattern: `get_settings()`, modify, `save()`

**Integration:**
```python
# In DatasetExecutor.create():
project = self.client.get_project(project_key)
dataset = project.create_managed_dataset(
    dataset_name=dataset_name,
    format_type=format_type
)

settings = dataset.get_settings()
settings.settings["description"] = attributes["description"]
settings.save()
```

---

## Acceptance Criteria

Wave 4 is complete when:

### Functional Requirements

- [ ] Can apply plan to create projects, datasets, recipes in Dataiku
- [ ] Can update existing resources (modify settings)
- [ ] Can delete resources no longer in config
- [ ] State file updated incrementally after each action
- [ ] Checkpoint created during apply for resume capability
- [ ] Can resume interrupted apply from checkpoint
- [ ] Rollback deletes created resources on failure
- [ ] Progress reported to console during apply
- [ ] `dataiku-iac apply` CLI command works end-to-end
- [ ] Auto-approve flag skips confirmation prompt
- [ ] Verbose mode shows detailed error information

### Quality Requirements

- [ ] >80% test coverage across all packages
- [ ] All integration tests pass
- [ ] Works with actual Dataiku instance (manual testing)
- [ ] Error messages are clear and actionable
- [ ] Documentation complete (API docs, usage guide)
- [ ] Demo script works end-to-end

### Demo Scenario

```bash
# 1. Create simple config
cat > demo.yml <<EOF
version: "1.0"
project:
  key: DEMO_IAC
  name: IaC Demo Project
  description: Created via apply command

datasets:
  - name: DEMO_DATA
    type: managed
    format_type: parquet
    description: Demo dataset
EOF

# 2. Plan
python -m dataikuapi.iac.cli.plan -c demo.yml -e dev
# Shows: 1 project + 1 dataset to create

# 3. Apply
export DATAIKU_DSS_URL="https://dss.example.com"
export DATAIKU_API_KEY="your-api-key"
python -m dataikuapi.iac.cli.apply -c demo.yml -e dev

# Output:
# ⏳ + project.DEMO_IAC
# ✓ + project.DEMO_IAC (1234ms)
# ⏳ + dataset.DEMO_IAC.DEMO_DATA
# ✓ + dataset.DEMO_IAC.DEMO_DATA (567ms)
#
# ✓ Apply completed successfully!
# - Actions completed: 2
# - Duration: 1.80s

# 4. Verify in Dataiku UI
# Project exists, dataset exists

# 5. Modify config (add description)
# Plan shows: 0 to create, 1 to update, 0 to destroy
# Apply updates the project

# 6. Remove dataset from config
# Plan shows: 0 to create, 0 to update, 1 to destroy
# Apply deletes the dataset
```

---

## Technical Risks & Mitigation

### Risk 1: Dataiku API Limitations

**Risk:** Some operations may not be possible via API (e.g., visual recipes, dashboards)

**Impact:** Medium - limits what can be managed as code

**Mitigation:**
- Start with well-supported resources (projects, datasets, Python/SQL recipes)
- Document limitations clearly
- Fall back to "managed externally" for unsupported resources
- Work with Dataiku team to identify API gaps

**Contingency:**
- Partial IaC coverage is still valuable
- Manual operations for advanced features
- Future API enhancements can be added incrementally

### Risk 2: State Corruption

**Risk:** State file gets out of sync with actual Dataiku state

**Impact:** High - could cause data loss or duplicate resources

**Mitigation:**
- Sync resources back from Dataiku after each operation (verify creation)
- Atomic state file writes (write to temp, then rename)
- State file backup before each apply
- Validation: compare state to Dataiku before apply

**Contingency:**
- State refresh command (Wave 5) to resync
- Manual state file editing (documented procedure)
- State reset and rebuild from Dataiku

### Risk 3: Rollback Failures

**Risk:** Rollback may fail to delete resources, leaving orphaned infrastructure

**Impact:** Medium - manual cleanup required, but no data loss

**Mitigation:**
- Best-effort rollback (log failures, continue)
- Clear documentation of what was/wasn't cleaned up
- Manual cleanup guide with specific resource IDs
- Dry-run mode to catch issues before apply

**Contingency:**
- Provide cleanup scripts for common scenarios
- Support can assist with manual cleanup
- Future: "drift detection" can identify orphaned resources

### Risk 4: Concurrent Apply Operations

**Risk:** Two users apply changes simultaneously, causing conflicts

**Impact:** High - could corrupt state or create duplicate resources

**Mitigation:**
- State locking (deferred to Wave 5, but architecture should support)
- Single-user usage in Wave 4 (documented limitation)
- Checkpoint files include environment name (prevents some conflicts)

**Contingency:**
- Document as known limitation for Wave 4
- Users must coordinate manually (don't run simultaneously)
- Wave 5 adds proper locking

### Risk 5: Long-Running Operations

**Risk:** Some operations (e.g., building large datasets) may timeout or hang

**Impact:** Medium - apply appears stuck, user interrupts

**Mitigation:**
- Set reasonable timeouts on API calls
- Progress reporting shows which action is running
- Checkpoint allows resume after interruption
- Don't wait for builds - just create resources

**Contingency:**
- Document timeout values
- User can resume with `--resume` flag
- Future: async operations with status polling

---

## Implementation Timeline

### Week 1: Executors & Core Engine (Days 1-5)

**Days 1-2: Resource Executors**
- Implement `ResourceExecutor` base class
- Implement `ProjectExecutor` (create, update, delete)
- Implement `DatasetExecutor` (managed and SQL datasets)
- Unit tests for executors

**Days 3-4: Apply Engine Core**
- Implement `ApplyEngine` class
- Implement action execution loop
- Implement incremental state updates
- Integration tests with mock client

**Day 5: Executor Registry**
- Implement `ExecutorRegistry`
- Wire up executors to engine
- Integration tests

**Deliverable:** Can execute actions (mocked), update state

---

### Week 2: Checkpoint & Rollback (Days 6-10)

**Days 6-7: Checkpoint System**
- Implement `CheckpointManager`
- Implement checkpoint serialization
- Implement resume capability
- Unit tests for checkpoint

**Days 8-9: Rollback Mechanism**
- Implement `RollbackManager`
- Implement reverse dependency ordering
- Implement best-effort cleanup
- Unit tests for rollback

**Day 10: Integration**
- Wire checkpoint into apply engine
- Wire rollback into apply engine
- Integration tests for resume and rollback

**Deliverable:** Can resume and rollback

---

### Week 3: Progress & CLI (Days 11-15)

**Days 11-12: Progress Reporting**
- Implement `ProgressReporter`
- Implement console output
- Implement JSON output
- Unit tests

**Days 13-14: CLI Apply Command**
- Implement `cli/apply.py`
- Implement argument parsing
- Implement confirmation prompt
- Integration tests

**Day 15: Recipe Executor**
- Implement `RecipeExecutor` (Python and SQL)
- Unit tests for recipes
- Integration tests

**Deliverable:** Full CLI working

---

### Week 4: Testing & Documentation (Days 16-20)

**Days 16-17: Integration Testing**
- End-to-end integration tests
- Test with actual Dataiku instance (manual)
- Fix bugs found in testing

**Days 18-19: Documentation**
- API documentation (docstrings)
- Usage guide (APPLY_GUIDE.md)
- Error handling guide
- Demo script

**Day 20: Polish & Release**
- Code review
- Coverage verification
- Commit and push
- Create completion report

**Deliverable:** Wave 4 complete, tested, documented

---

## Effort Estimate

**Total Effort:** ~80-100 hours (4 weeks @ 20-25 hours/week)

**Comparison to Previous Waves:**
- Wave 1: ~60-80 hours (state management foundation)
- Wave 3: ~40-60 hours (plan generation, less complexity)
- **Wave 4: ~80-100 hours** (highest complexity due to real API operations)

**Complexity Factors:**
- **Higher:** Real Dataiku API operations (can't be fully mocked)
- **Higher:** Error handling and rollback logic
- **Higher:** Checkpoint/resume state management
- **Similar:** Number of packages and classes
- **Lower:** Pattern established by previous waves

**Confidence Level:** Medium-High
- Executors follow clear patterns from sync classes
- Apply engine follows standard orchestration patterns
- Checkpoint similar to state management (already done)
- Main risk is Dataiku API integration (requires real testing)

---

## Next Steps

### Immediate (Before Implementation)

1. **Review and approve** this planning document
2. **Identify test Dataiku instance** for integration testing
3. **Set up test environment** with sample projects
4. **Confirm API access** (verify credentials work)
5. **Create feature branch** `feature/wave4-apply-execution`

### Week 1 Start

1. **Implement Package 2** (Resource Executors) first
   - Most critical component
   - Establishes patterns for rest of wave
   - Can be tested independently

2. **Set up integration test infrastructure**
   - Mock DSSClient for unit tests
   - Test Dataiku instance for integration tests
   - Fixture data

3. **Daily standups** to track progress and risks

### Post-Wave 4

1. **Wave 5 Planning** - State refresh, import, drift detection
2. **Beta testing** with internal users
3. **Documentation** - User guide, tutorials
4. **Performance testing** - Large projects

---

## Open Questions

### Question 1: Dataiku API Client Patterns

**Question:** Do we need to follow any specific patterns for API operations?

**Context:** Existing codebase has patterns like `get_settings()`, modify, `save()`. Should we always follow this?

**Decision Needed:** Yes/No + any exceptions

**Impact:** Affects executor implementation

---

### Question 2: Rollback Scope

**Question:** Should rollback be configurable (e.g., rollback only creates, or also updates)?

**Context:** Rolling back an update means reverting to previous settings, which is complex.

**Decision Needed:** Rollback scope for Wave 4

**Impact:** Affects rollback implementation complexity

**Recommendation:** Wave 4 rollback only CREATEs. Updates/deletes don't rollback (too complex).

---

### Question 3: Progress Output Detail

**Question:** How verbose should console output be?

**Context:** Terraform shows every action. We could show more/less detail.

**Decision Needed:** Default verbosity level

**Impact:** User experience

**Recommendation:** Show action + result by default. `--verbose` shows API calls, errors.

---

### Question 4: State Backup

**Question:** Should we automatically backup state before apply?

**Context:** Could prevent data loss if apply corrupts state.

**Decision Needed:** Auto-backup yes/no

**Impact:** File management, restore procedure

**Recommendation:** Yes - backup to `.dataiku-iac/backups/state-{timestamp}.json`

---

## Success Criteria Summary

Wave 4 succeeds when:

1. ✅ Can create project + datasets + recipes via `apply` command
2. ✅ Can update existing resources by modifying config
3. ✅ Can delete resources by removing from config
4. ✅ State file updated incrementally (can inspect mid-apply)
5. ✅ Can resume interrupted apply from checkpoint
6. ✅ Rollback deletes created resources on failure
7. ✅ Progress visible in console during apply
8. ✅ Works with real Dataiku instance (manual verification)
9. ✅ >80% test coverage
10. ✅ All integration tests pass
11. ✅ Documentation complete
12. ✅ Demo script works end-to-end

---

## Appendix: File Structure

```
dataikuapi/iac/
├── apply/                          # NEW - Wave 4
│   ├── __init__.py
│   ├── engine.py                  # ApplyEngine, ApplyResult, Checkpoint
│   ├── checkpoint.py              # CheckpointManager
│   ├── rollback.py                # RollbackManager
│   ├── progress.py                # ProgressReporter, ProgressEvent
│   └── executors/                 # Resource executors
│       ├── __init__.py            # ExecutorRegistry
│       ├── base.py                # ResourceExecutor (abstract)
│       ├── project.py             # ProjectExecutor
│       ├── dataset.py             # DatasetExecutor
│       └── recipe.py              # RecipeExecutor
├── cli/
│   ├── plan.py                    # Wave 3
│   └── apply.py                   # NEW - Wave 4
├── exceptions.py                  # Add ApplyError, ExecutionError, etc.
└── ...

tests/iac/
├── test_apply_engine.py           # NEW - Wave 4
├── test_executors.py              # NEW - Wave 4
├── test_checkpoint.py             # NEW - Wave 4
├── test_rollback.py               # NEW - Wave 4
├── test_progress.py               # NEW - Wave 4
└── test_integration_apply.py      # NEW - Wave 4

demos/
└── week4_apply_workflow.py        # NEW - Wave 4 demo

docs/
└── APPLY_GUIDE.md                 # NEW - Usage guide
```

**Total New Files:** ~15 implementation + ~6 test + 1 demo + 1 doc = ~23 files

**Estimated Lines of Code:**
- Implementation: ~2,000-2,500 lines
- Tests: ~2,500-3,000 lines
- **Total: ~4,500-5,500 lines** (similar to Wave 3)

---

**Document Version:** 0.1.0
**Status:** Ready for Review
**Next Review:** After approval, before implementation

**Prepared by:** Claude (Senior Software Engineer)
**Date:** 2025-11-27
