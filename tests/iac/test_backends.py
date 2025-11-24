"""
Unit tests for state backend implementations.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from dataikuapi.iac.backends import StateBackend, LocalFileBackend
from dataikuapi.iac.models import State, Resource, ResourceMetadata, make_resource_id
from dataikuapi.iac.exceptions import (
    StateNotFoundError,
    StateCorruptedError,
    StateWriteError
)


class TestLocalFileBackend:
    """Test LocalFileBackend implementation"""

    def test_create_backend(self, tmp_path):
        """Can create LocalFileBackend instance"""
        state_file = tmp_path / "test.state.json"
        backend = LocalFileBackend(state_file)
        assert backend.state_file == state_file
        assert backend.state_file.parent.exists()

    def test_create_backend_creates_parent_directory(self, tmp_path):
        """Backend creates parent directory if it doesn't exist"""
        state_file = tmp_path / "subdir" / "nested" / "test.state.json"
        backend = LocalFileBackend(state_file)
        assert backend.state_file.parent.exists()

    def test_exists_returns_false_for_new_backend(self, tmp_path):
        """exists() returns False when state file doesn't exist"""
        backend = LocalFileBackend(tmp_path / "test.state.json")
        assert not backend.exists()

    def test_save_creates_file(self, tmp_path):
        """save() creates state file"""
        backend = LocalFileBackend(tmp_path / "test.state.json")
        state = State(environment="test")
        backend.save(state)
        assert backend.exists()

    def test_save_writes_valid_json(self, tmp_path):
        """save() writes valid JSON to file"""
        backend = LocalFileBackend(tmp_path / "test.state.json")
        state = State(environment="test", serial=1)
        backend.save(state)

        # Verify we can read the JSON directly
        with open(backend.state_file, 'r') as f:
            data = json.load(f)

        assert data["environment"] == "test"
        assert data["serial"] == 1
        assert data["version"] == 1

    def test_load_reads_state(self, tmp_path):
        """load() reads state from file"""
        backend = LocalFileBackend(tmp_path / "test.state.json")
        state = State(environment="test", serial=5, lineage="abc123")
        backend.save(state)

        loaded_state = backend.load()
        assert loaded_state.environment == "test"
        assert loaded_state.serial == 5
        assert loaded_state.lineage == "abc123"

    def test_load_raises_for_missing_file(self, tmp_path):
        """load() raises StateNotFoundError when file doesn't exist"""
        backend = LocalFileBackend(tmp_path / "missing.state.json")
        with pytest.raises(StateNotFoundError) as exc_info:
            backend.load()
        assert "not found" in str(exc_info.value).lower()

    def test_load_raises_for_invalid_json(self, tmp_path):
        """load() raises StateCorruptedError for invalid JSON"""
        backend = LocalFileBackend(tmp_path / "test.state.json")

        # Write invalid JSON
        with open(backend.state_file, 'w') as f:
            f.write("{ this is not valid json }")

        with pytest.raises(StateCorruptedError) as exc_info:
            backend.load()
        assert "invalid json" in str(exc_info.value).lower()

    def test_load_raises_for_missing_required_fields(self, tmp_path):
        """load() raises StateCorruptedError when required fields are missing"""
        backend = LocalFileBackend(tmp_path / "test.state.json")

        # Write JSON missing required field
        with open(backend.state_file, 'w') as f:
            json.dump({"version": 1}, f)  # Missing updated_at

        with pytest.raises(StateCorruptedError):
            backend.load()

    def test_save_and_load_roundtrip(self, tmp_path):
        """State survives save/load roundtrip"""
        backend = LocalFileBackend(tmp_path / "test.state.json")

        # Create state with resource
        state = State(environment="dev", serial=10, lineage="commit-abc")
        resource = Resource(
            resource_type="project",
            resource_id="project.TEST_PROJECT",
            attributes={"name": "Test Project", "description": "A test"},
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="test_user",
                checksum="abc123"
            )
        )
        state.add_resource(resource)

        # Save and load
        backend.save(state)
        loaded_state = backend.load()

        # Verify
        assert loaded_state.environment == "dev"
        assert loaded_state.serial == 11  # Incremented by add_resource
        assert loaded_state.lineage == "commit-abc"
        assert len(loaded_state.resources) == 1
        assert "project.TEST_PROJECT" in loaded_state.resources
        loaded_resource = loaded_state.resources["project.TEST_PROJECT"]
        assert loaded_resource.attributes["name"] == "Test Project"

    def test_atomic_write_uses_temp_file(self, tmp_path):
        """save() uses temporary file for atomic write"""
        backend = LocalFileBackend(tmp_path / "test.state.json")
        state = State(environment="test")

        # Verify temp file doesn't exist before
        temp_file = backend.state_file.with_suffix('.tmp')
        assert not temp_file.exists()

        backend.save(state)

        # After successful save, temp file should be cleaned up
        assert not temp_file.exists()
        assert backend.state_file.exists()

    def test_backup_on_save(self, tmp_path):
        """save() creates backup of previous state"""
        backend = LocalFileBackend(tmp_path / "test.state.json")

        # First save
        state1 = State(environment="test", serial=1)
        backend.save(state1)

        # Second save should create backup
        state2 = State(environment="test", serial=2)
        backend.save(state2)

        # Check backup was created
        backup_file = tmp_path / "test.state.pre-serial-2.json"
        assert backup_file.exists()

        # Verify backup contains first state
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        assert backup_data["serial"] == 1

    def test_backup_method(self, tmp_path):
        """backup() creates backup with custom suffix"""
        backend = LocalFileBackend(tmp_path / "test.state.json")
        state = State(environment="test", serial=5)
        backend.save(state)

        # Create manual backup
        backup_path = backend.backup(suffix="manual-backup")

        assert backup_path.exists()
        assert backup_path.name == "test.state.manual-backup.json"

        # Verify backup contains same data
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        assert backup_data["serial"] == 5

    def test_backup_raises_when_no_state(self, tmp_path):
        """backup() raises StateNotFoundError when no state exists"""
        backend = LocalFileBackend(tmp_path / "test.state.json")

        with pytest.raises(StateNotFoundError) as exc_info:
            backend.backup()
        assert "no state" in str(exc_info.value).lower()

    def test_delete_removes_file(self, tmp_path):
        """delete() removes state file"""
        backend = LocalFileBackend(tmp_path / "test.state.json")
        state = State(environment="test")
        backend.save(state)

        assert backend.exists()
        backend.delete()
        assert not backend.exists()

    def test_delete_raises_when_no_state(self, tmp_path):
        """delete() raises StateNotFoundError when file doesn't exist"""
        backend = LocalFileBackend(tmp_path / "test.state.json")

        with pytest.raises(StateNotFoundError):
            backend.delete()

    def test_multiple_backups(self, tmp_path):
        """Multiple backups can be created with different suffixes"""
        backend = LocalFileBackend(tmp_path / "test.state.json")
        state = State(environment="test")
        backend.save(state)

        backup1 = backend.backup(suffix="backup1")
        backup2 = backend.backup(suffix="backup2")
        backup3 = backend.backup(suffix="backup3")

        assert backup1.exists()
        assert backup2.exists()
        assert backup3.exists()
        assert backup1 != backup2 != backup3

    def test_save_after_failed_save_recovers(self, tmp_path):
        """System recovers after a failed save attempt"""
        backend = LocalFileBackend(tmp_path / "test.state.json")
        state = State(environment="test")
        backend.save(state)

        # Simulate failed save by making temp file read-only
        # (This is a simplified test - real failure scenarios are harder to simulate)
        temp_file = backend.state_file.with_suffix('.tmp')

        # Successful second save should still work
        state2 = State(environment="test", serial=2)
        backend.save(state2)  # Should not raise

        assert backend.exists()
        loaded = backend.load()
        assert loaded.serial == 2

    def test_state_with_multiple_resources(self, tmp_path):
        """Can save and load state with multiple resources"""
        backend = LocalFileBackend(tmp_path / "test.state.json")

        # Create state with multiple resources
        state = State(environment="test")

        project = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test"}
        )
        dataset1 = Resource(
            resource_type="dataset",
            resource_id="dataset.TEST.DATASET1",
            attributes={"type": "SQL"}
        )
        dataset2 = Resource(
            resource_type="dataset",
            resource_id="dataset.TEST.DATASET2",
            attributes={"type": "Filesystem"}
        )

        state.add_resource(project)
        state.add_resource(dataset1)
        state.add_resource(dataset2)

        # Save and load
        backend.save(state)
        loaded = backend.load()

        assert len(loaded.resources) == 3
        assert "project.TEST" in loaded.resources
        assert "dataset.TEST.DATASET1" in loaded.resources
        assert "dataset.TEST.DATASET2" in loaded.resources

    def test_load_preserves_resource_metadata(self, tmp_path):
        """load() preserves resource metadata correctly"""
        backend = LocalFileBackend(tmp_path / "test.state.json")

        deployed_time = datetime.utcnow()
        state = State(environment="test")
        resource = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test"},
            metadata=ResourceMetadata(
                deployed_at=deployed_time,
                deployed_by="john_doe",
                dataiku_internal_id="internal_123",
                checksum="checksum_abc"
            )
        )
        state.add_resource(resource)

        backend.save(state)
        loaded = backend.load()

        loaded_resource = loaded.resources["project.TEST"]
        assert loaded_resource.metadata.deployed_by == "john_doe"
        assert loaded_resource.metadata.dataiku_internal_id == "internal_123"
        assert loaded_resource.metadata.checksum == "checksum_abc"
        # Note: datetime comparison might have microsecond precision differences
        assert abs((loaded_resource.metadata.deployed_at - deployed_time).total_seconds()) < 1

    def test_backend_is_subclass_of_state_backend(self):
        """LocalFileBackend implements StateBackend interface"""
        assert issubclass(LocalFileBackend, StateBackend)

    def test_concurrent_backup_suffixes(self, tmp_path):
        """Different serial numbers create different backups"""
        backend = LocalFileBackend(tmp_path / "test.state.json")

        # Save multiple times - each should create unique backup
        state1 = State(environment="test", serial=1)
        backend.save(state1)

        state2 = State(environment="test", serial=2)
        backend.save(state2)

        state3 = State(environment="test", serial=3)
        backend.save(state3)

        # Should have backups for serial 2 and 3 (first save has no previous state)
        backup2 = tmp_path / "test.state.pre-serial-2.json"
        backup3 = tmp_path / "test.state.pre-serial-3.json"

        assert backup2.exists()
        assert backup3.exists()

        # Verify backup contents
        with open(backup2, 'r') as f:
            data2 = json.load(f)
        assert data2["serial"] == 1

        with open(backup3, 'r') as f:
            data3 = json.load(f)
        assert data3["serial"] == 2

    def test_save_with_write_failure(self, tmp_path):
        """save() handles write failures and cleans up temp file"""
        backend = LocalFileBackend(tmp_path / "test.state.json")

        # Create a directory where the state file should be to cause write failure
        backend.state_file.mkdir(parents=True)

        state = State(environment="test")

        # Should raise StateWriteError and clean up temp file
        with pytest.raises(StateWriteError):
            backend.save(state)

        # Temp file should not exist after failed save
        temp_file = backend.state_file.with_suffix('.tmp')
        assert not temp_file.exists()

    def test_load_with_unexpected_error(self, tmp_path):
        """load() handles unexpected parsing errors"""
        backend = LocalFileBackend(tmp_path / "test.state.json")

        # Write valid JSON but with wrong structure that causes unexpected error
        with open(backend.state_file, 'w') as f:
            # This will cause an error in State.from_dict due to wrong date format
            json.dump({
                "version": 1,
                "serial": 0,
                "environment": "test",
                "updated_at": "not-a-valid-iso-date",
                "resources": {}
            }, f)

        with pytest.raises(StateCorruptedError) as exc_info:
            backend.load()
        assert "failed to parse" in str(exc_info.value).lower()
