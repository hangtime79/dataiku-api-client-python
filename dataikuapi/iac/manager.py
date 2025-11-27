"""
State Manager - Main orchestrator for Dataiku IaC state management.
"""

from dataikuapi import DSSClient

from .models.state import State, Resource, make_resource_id
from .backends.base import StateBackend
from .sync.project import ProjectSync
from .sync.dataset import DatasetSync
from .sync.recipe import RecipeSync


class StateManager:
    """
    Main orchestrator for state management.

    Coordinates:
        - Loading/saving state via backend
        - Syncing with Dataiku
        - Comparing states

    Example:
        >>> from dataikuapi import DSSClient
        >>> from dataikuapi.iac.backends.local import LocalFileBackend
        >>> from dataikuapi.iac.manager import StateManager
        >>>
        >>> client = DSSClient("https://dataiku.company.com", "api-key")
        >>> backend = LocalFileBackend(Path(".dataiku/state/prod.state.json"))
        >>> manager = StateManager(backend, client, "prod")
        >>>
        >>> # Sync project from Dataiku
        >>> state = manager.sync_project("MY_PROJECT", include_children=True)
        >>> manager.save_state(state)
    """

    def __init__(self,
                 backend: StateBackend,
                 client: DSSClient,
                 environment: str):
        """
        Initialize StateManager.

        Args:
            backend: State storage backend
            client: Dataiku API client
            environment: Target environment name (e.g., "dev", "prod")
        """
        self.backend = backend
        self.client = client
        self.environment = environment

        # Initialize sync engines
        self.project_sync = ProjectSync(client)
        self.dataset_sync = DatasetSync(client)
        self.recipe_sync = RecipeSync(client)

        # Registry for resource type delegation
        self._sync_registry = {
            "project": self.project_sync,
            "dataset": self.dataset_sync,
            "recipe": self.recipe_sync,
        }

    def load_state(self) -> State:
        """
        Load state from backend.

        Returns:
            State object, or empty state if doesn't exist

        Example:
            >>> state = manager.load_state()
            >>> print(f"Loaded {len(state.resources)} resources")
        """
        if self.backend.exists():
            return self.backend.load()
        else:
            # Return empty state
            return State(environment=self.environment)

    def save_state(self, state: State) -> None:
        """
        Save state to backend.

        Args:
            state: State to persist

        Raises:
            StateWriteError: If save fails

        Example:
            >>> manager.save_state(state)
        """
        state.environment = self.environment
        self.backend.save(state)

    def sync_resource(self, resource_id: str) -> Resource:
        """
        Sync single resource from Dataiku.

        Args:
            resource_id: Resource to sync (e.g., "project.MY_PROJECT")

        Returns:
            Updated Resource object

        Raises:
            ValueError: If resource type is unknown
            ResourceNotFoundError: If resource doesn't exist in Dataiku

        Example:
            >>> resource = manager.sync_resource("dataset.MY_PROJECT.CUSTOMERS")
        """
        resource_type = resource_id.split('.')[0]

        if resource_type not in self._sync_registry:
            raise ValueError(f"Unknown resource type: {resource_type}")

        sync_engine = self._sync_registry[resource_type]
        return sync_engine.fetch(resource_id)

    def sync_project(self, project_key: str, include_children: bool = True) -> State:
        """
        Sync entire project and optionally its datasets/recipes.

        Args:
            project_key: Project to sync
            include_children: Include datasets and recipes (default: True)

        Returns:
            State with synced resources

        Raises:
            ResourceNotFoundError: If project doesn't exist

        Example:
            >>> state = manager.sync_project("MY_PROJECT", include_children=True)
            >>> print(f"Synced {len(state.resources)} resources")
        """
        state = State(environment=self.environment)

        # Sync project
        project_id = make_resource_id("project", project_key)
        project_resource = self.project_sync.fetch(project_id)
        state.add_resource(project_resource)

        if include_children:
            # Sync datasets
            try:
                for dataset_resource in self.dataset_sync.list_all(project_key):
                    state.add_resource(dataset_resource)
            except Exception:
                # Continue if datasets fail (project might have none)
                pass

            # Sync recipes
            try:
                for recipe_resource in self.recipe_sync.list_all(project_key):
                    state.add_resource(recipe_resource)
            except Exception:
                # Continue if recipes fail (project might have none)
                pass

        return state

    def sync_all(self) -> State:
        """
        Sync all accessible projects and resources.

        Returns:
            State with all synced resources

        Example:
            >>> state = manager.sync_all()
            >>> projects = state.list_resources("project")
            >>> print(f"Found {len(projects)} projects")
        """
        state = State(environment=self.environment)

        # Get all projects
        for project_resource in self.project_sync.list_all():
            state.add_resource(project_resource)

            project_key = project_resource.project_key

            # Get datasets and recipes for each project
            try:
                for dataset_resource in self.dataset_sync.list_all(project_key):
                    state.add_resource(dataset_resource)
            except Exception:
                # Continue if datasets fail
                pass

            try:
                for recipe_resource in self.recipe_sync.list_all(project_key):
                    state.add_resource(recipe_resource)
            except Exception:
                # Continue if recipes fail
                pass

        return state
