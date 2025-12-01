"""Unit tests for flow graph extraction methods."""
import pytest
from unittest.mock import Mock, MagicMock
from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
from dataikuapi.iac.workflows.discovery.models import BlockContents


@pytest.fixture
def mock_crawler():
    """Create a mock FlowCrawler."""
    crawler = Mock()
    crawler.client = Mock()
    return crawler


@pytest.fixture
def identifier(mock_crawler):
    """Create a BlockIdentifier with mock crawler."""
    return BlockIdentifier(mock_crawler)


@pytest.fixture
def sample_boundary():
    """Sample boundary with inputs/outputs."""
    return {
        "inputs": ["input_ds1", "input_ds2"],
        "outputs": ["output_ds"],
        "internals": ["internal_ds1"],
        "is_valid": True
    }


@pytest.fixture
def sample_contents():
    """Sample block contents."""
    return BlockContents(
        datasets=["internal_ds1", "internal_ds2"],
        recipes=["compute_A", "compute_B"]
    )


class TestExtractGraphNodes:
    """Tests for _extract_graph_nodes method."""

    def test_extracts_all_node_types(self, identifier, sample_boundary, sample_contents):
        """Test extraction of inputs, outputs, internal datasets, and recipes."""
        nodes = identifier._extract_graph_nodes(sample_boundary, sample_contents)

        # Extract IDs for easier assertion
        node_ids = [n["id"] for n in nodes]
        node_types = {n["id"]: n["type"] for n in nodes}

        # Verify all inputs present
        assert "input_ds1" in node_ids
        assert "input_ds2" in node_ids

        # Verify output present
        assert "output_ds" in node_ids

        # Verify internal datasets present
        assert "internal_ds1" in node_ids
        assert "internal_ds2" in node_ids

        # Verify recipes present
        assert "compute_A" in node_ids
        assert "compute_B" in node_ids

        # Verify correct types
        assert node_types["input_ds1"] == "DATASET"
        assert node_types["compute_A"] == "RECIPE"

    def test_assigns_correct_roles(self, identifier, sample_boundary, sample_contents):
        """Test that nodes have correct role assignments."""
        nodes = identifier._extract_graph_nodes(sample_boundary, sample_contents)

        node_roles = {n["id"]: n["role"] for n in nodes}

        assert node_roles["input_ds1"] == "input"
        assert node_roles["output_ds"] == "output"
        assert node_roles["internal_ds1"] == "internal"
        assert node_roles["compute_A"] == "internal"

    def test_handles_empty_boundary(self, identifier):
        """Test graceful handling of empty inputs/outputs."""
        boundary = {"inputs": [], "outputs": [], "internals": []}
        contents = BlockContents(datasets=[], recipes=[])

        nodes = identifier._extract_graph_nodes(boundary, contents)

        assert nodes == []

    def test_handles_missing_keys(self, identifier):
        """Test graceful handling of missing boundary keys."""
        boundary = {}  # No inputs/outputs/internals keys
        contents = BlockContents(datasets=["ds1"], recipes=["r1"])

        nodes = identifier._extract_graph_nodes(boundary, contents)

        # Should still get internal items
        node_ids = [n["id"] for n in nodes]
        assert "ds1" in node_ids
        assert "r1" in node_ids
