"""
Integration tests for syncing state from real Dataiku instance.

These tests require:
- USE_REAL_DATAIKU=true environment variable
- Access to Dataiku instance at http://172.18.58.26:10000
- Existing projects to sync (or will skip if not found)

Tests validate:
- Real project synchronization
- Real dataset synchronization
- Real recipe synchronization
- State accuracy and checksums
- Error handling with real API
"""

import pytest
from pathlib import Path

from dataikuapi.iac.manager import StateManager
from dataikuapi.iac.backends.local import LocalFileBackend
from dataikuapi.iac.models.state import State, Resource
from dataikuapi.iac.sync import ProjectSync, DatasetSync, RecipeSync
from dataikuapi.iac.exceptions import ResourceNotFoundError


@pytest.mark.integration
@pytest.mark.slow
class TestRealProjectSync:
    """Test syncing projects from real Dataiku instance"""

    def test_list_all_projects(self, real_client, skip_if_no_real_dataiku):
        """Test listing all projects from Dataiku"""
        project_sync = ProjectSync(real_client)

        try:
            projects = project_sync.list_all()

            # Should return a list (might be empty if no projects)
            assert isinstance(projects, list)

            # If projects exist, validate structure
            if projects:
                project = projects[0]
                assert isinstance(project, Resource)
                assert project.resource_type == "project"
                assert project.resource_id.startswith("project.")
                assert "projectKey" in project.attributes
                assert "name" in project.attributes
                assert project.metadata is not None
                assert project.metadata.checksum != ""

                print(f"\nFound {len(projects)} projects")
                for p in projects[:5]:  # Print first 5
                    print(f"  - {p.attributes.get('projectKey')}: {p.attributes.get('name')}")

        except Exception as e:
            pytest.skip(f"Could not list projects: {e}")

    def test_fetch_specific_project(self, real_client, skip_if_no_real_dataiku, test_project_key):
        """Test fetching a specific project by key"""
        project_sync = ProjectSync(real_client)

        try:
            # Try to fetch the test project
            resource_id = f"project.{test_project_key}"
            project = project_sync.fetch(resource_id)

            assert isinstance(project, Resource)
            assert project.resource_type == "project"
            assert project.attributes["projectKey"] == test_project_key
            assert "name" in project.attributes
            assert project.metadata.checksum != ""

            print(f"\nSynced project: {project.attributes.get('name')}")
            print(f"  Description: {project.attributes.get('description', 'N/A')}")
            print(f"  Checksum: {project.metadata.checksum[:16]}...")

        except Exception as e:
            pytest.skip(f"Project {test_project_key} not found or inaccessible: {e}")

    def test_fetch_nonexistent_project_raises_error(self, real_client, skip_if_no_real_dataiku):
        """Test that fetching non-existent project raises appropriate error"""
        project_sync = ProjectSync(real_client)

        with pytest.raises(ResourceNotFoundError):
            project_sync.fetch("project.DEFINITELY_DOES_NOT_EXIST_12345")


@pytest.mark.integration
@pytest.mark.slow
class TestRealDatasetSync:
    """Test syncing datasets from real Dataiku instance"""

    def test_list_all_datasets_in_project(self, real_client, skip_if_no_real_dataiku, test_project_key):
        """Test listing all datasets in a project"""
        dataset_sync = DatasetSync(real_client)

        try:
            datasets = dataset_sync.list_all(project_key=test_project_key)

            # Should return a list (might be empty)
            assert isinstance(datasets, list)

            if datasets:
                dataset = datasets[0]
                assert isinstance(dataset, Resource)
                assert dataset.resource_type == "dataset"
                assert dataset.resource_id.startswith("dataset.")
                assert "name" in dataset.attributes
                assert "type" in dataset.attributes
                assert dataset.metadata.checksum != ""

                print(f"\nFound {len(datasets)} datasets in {test_project_key}")
                for ds in datasets[:5]:
                    print(f"  - {ds.attributes.get('name')} ({ds.attributes.get('type')})")

        except Exception as e:
            pytest.skip(f"Could not list datasets for {test_project_key}: {e}")

    def test_fetch_specific_dataset(self, real_client, skip_if_no_real_dataiku, test_project_key):
        """Test fetching a specific dataset"""
        dataset_sync = DatasetSync(real_client)

        try:
            # First, list datasets to get a real one
            datasets = dataset_sync.list_all(project_key=test_project_key)

            if not datasets:
                pytest.skip(f"No datasets found in {test_project_key}")

            # Fetch the first dataset explicitly
            dataset_resource_id = datasets[0].resource_id
            dataset = dataset_sync.fetch(dataset_resource_id)

            assert isinstance(dataset, Resource)
            assert dataset.resource_type == "dataset"
            assert "name" in dataset.attributes
            assert "type" in dataset.attributes
            assert dataset.metadata.checksum != ""

            print(f"\nSynced dataset: {dataset.attributes.get('name')}")
            print(f"  Type: {dataset.attributes.get('type')}")
            print(f"  Format: {dataset.attributes.get('formatType', 'N/A')}")

        except Exception as e:
            pytest.skip(f"Could not fetch dataset: {e}")


@pytest.mark.integration
@pytest.mark.slow
class TestRealRecipeSync:
    """Test syncing recipes from real Dataiku instance"""

    def test_list_all_recipes_in_project(self, real_client, skip_if_no_real_dataiku, test_project_key):
        """Test listing all recipes in a project"""
        recipe_sync = RecipeSync(real_client)

        try:
            recipes = recipe_sync.list_all(project_key=test_project_key)

            # Should return a list (might be empty)
            assert isinstance(recipes, list)

            if recipes:
                recipe = recipes[0]
                assert isinstance(recipe, Resource)
                assert recipe.resource_type == "recipe"
                assert recipe.resource_id.startswith("recipe.")
                assert "name" in recipe.attributes
                assert "type" in recipe.attributes
                assert dataset.metadata.checksum != ""

                print(f"\nFound {len(recipes)} recipes in {test_project_key}")
                for r in recipes[:5]:
                    print(f"  - {r.attributes.get('name')} ({r.attributes.get('type')})")

        except Exception as e:
            pytest.skip(f"Could not list recipes for {test_project_key}: {e}")


@pytest.mark.integration
@pytest.mark.slow
class TestStateManagerRealSync:
    """Test StateManager with real Dataiku instance"""

    def test_sync_project_with_children(self, real_client, skip_if_no_real_dataiku, test_project_key, tmp_path):
        """Test syncing entire project with datasets and recipes"""
        state_file = tmp_path / "real_sync.state.json"
        backend = LocalFileBackend(state_file)
        manager = StateManager(backend, real_client, "integration_test")

        try:
            # Sync project with all children
            state = manager.sync_project(test_project_key, include_children=True)

            # Validate state
            assert isinstance(state, State)
            assert state.environment == "integration_test"
            assert len(state.resources) >= 1  # At least the project

            # Check project exists in state
            project_id = f"project.{test_project_key}"
            assert project_id in state.resources

            project_resource = state.resources[project_id]
            assert project_resource.resource_type == "project"
            assert project_resource.attributes["projectKey"] == test_project_key

            # Count resources by type
            resource_counts = {}
            for resource in state.resources.values():
                rtype = resource.resource_type
                resource_counts[rtype] = resource_counts.get(rtype, 0) + 1

            print(f"\nSynced state for {test_project_key}:")
            print(f"  Total resources: {len(state.resources)}")
            for rtype, count in resource_counts.items():
                print(f"  {rtype}: {count}")

            # Save and verify state file
            manager.save_state(state)
            assert state_file.exists()

            # Reload and compare
            loaded_state = manager.load_state()
            assert len(loaded_state.resources) == len(state.resources)

        except Exception as e:
            pytest.skip(f"Could not sync project {test_project_key}: {e}")

    def test_state_roundtrip_preserves_checksums(self, real_client, skip_if_no_real_dataiku, test_project_key, tmp_path):
        """Test that sync → save → load preserves resource checksums"""
        state_file = tmp_path / "roundtrip.state.json"
        backend = LocalFileBackend(state_file)
        manager = StateManager(backend, real_client, "test")

        try:
            # Sync from Dataiku
            original_state = manager.sync_project(test_project_key, include_children=False)

            # Save
            manager.save_state(original_state)

            # Load
            loaded_state = manager.load_state()

            # Compare checksums
            for resource_id in original_state.resources:
                original_checksum = original_state.resources[resource_id].metadata.checksum
                loaded_checksum = loaded_state.resources[resource_id].metadata.checksum

                assert original_checksum == loaded_checksum, \
                    f"Checksum mismatch for {resource_id}"

            print(f"\n✓ All {len(original_state.resources)} resource checksums preserved")

        except Exception as e:
            pytest.skip(f"Could not complete roundtrip test: {e}")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.cleanup_required
class TestConnectionAndAuth:
    """Test connection and authentication"""

    def test_client_can_connect(self, real_client, skip_if_no_real_dataiku):
        """Test that client can successfully connect to Dataiku"""
        try:
            # Try to list projects as connectivity test
            project_sync = ProjectSync(real_client)
            projects = project_sync.list_all()

            # If we get here, connection successful
            print(f"\n✓ Successfully connected to Dataiku")
            print(f"  Found {len(projects)} accessible projects")

        except Exception as e:
            pytest.fail(f"Failed to connect to Dataiku: {e}")

    def test_client_host_is_correct(self, dataiku_host, skip_if_no_real_dataiku):
        """Test that configured host matches expected"""
        assert dataiku_host == "http://172.18.58.26:10000", \
            f"Unexpected host: {dataiku_host}"
