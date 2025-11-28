"""Tests for Discovery Agent custom exceptions."""

import pytest


class TestDiscoveryExceptions:
    """Test suite for custom exceptions."""

    def test_discovery_error_base(self):
        """Test base DiscoveryError exception."""
        from dataikuapi.iac.workflows.discovery.exceptions import DiscoveryError

        error = DiscoveryError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_invalid_block_error(self):
        """Test InvalidBlockError exception."""
        from dataikuapi.iac.workflows.discovery.exceptions import InvalidBlockError

        error = InvalidBlockError("Zone is not a valid block")
        assert str(error) == "Zone is not a valid block"
        assert isinstance(error, Exception)

    def test_invalid_block_error_with_reason(self):
        """Test InvalidBlockError with reason."""
        from dataikuapi.iac.workflows.discovery.exceptions import InvalidBlockError

        zone_name = "test_zone"
        reason = "No outputs found"
        error = InvalidBlockError(f"Zone '{zone_name}' is invalid: {reason}")

        assert zone_name in str(error)
        assert reason in str(error)

    def test_block_not_found_error(self):
        """Test BlockNotFoundError exception."""
        from dataikuapi.iac.workflows.discovery.exceptions import BlockNotFoundError

        block_id = "MISSING_BLOCK"
        error = BlockNotFoundError(f"Block '{block_id}' not found")

        assert block_id in str(error)

    def test_catalog_write_error(self):
        """Test CatalogWriteError exception."""
        from dataikuapi.iac.workflows.discovery.exceptions import CatalogWriteError

        error = CatalogWriteError("Failed to write to catalog")
        assert "catalog" in str(error).lower()

    def test_schema_extraction_error(self):
        """Test SchemaExtractionError exception."""
        from dataikuapi.iac.workflows.discovery.exceptions import SchemaExtractionError

        dataset_name = "test_dataset"
        error = SchemaExtractionError(f"Failed to extract schema from {dataset_name}")

        assert dataset_name in str(error)

    def test_exception_with_cause(self):
        """Test exception chaining with cause."""
        from dataikuapi.iac.workflows.discovery.exceptions import (
            DiscoveryError,
            CatalogWriteError,
        )

        original = ValueError("Original error")
        try:
            raise CatalogWriteError("Catalog write failed") from original
        except CatalogWriteError as wrapped:
            assert isinstance(wrapped, CatalogWriteError)
            assert wrapped.__cause__ == original
