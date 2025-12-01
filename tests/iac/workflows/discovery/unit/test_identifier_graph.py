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


class TestExtractGraphEdges:
    """Tests for _extract_graph_edges method."""

    @pytest.fixture
    def mock_recipe_with_io(self):
        """Mock recipe with inputs and outputs."""
        recipe = MagicMock()
        settings = MagicMock()
        settings.get_raw.return_value = {
            "type": "python",
            "params": {"engineType": "DSS"},
            "inputs": {
                "main": {"ref": "input_ds"}
            },
            "outputs": {
                "main": {"ref": "output_ds"}
            }
        }
        recipe.get_settings.return_value = settings
        return recipe

    @pytest.fixture
    def mock_project(self, mock_recipe_with_io):
        """Mock project that returns recipes."""
        project = Mock()
        project.get_recipe.return_value = mock_recipe_with_io
        return project

    def test_creates_bidirectional_edges(self, identifier, mock_project):
        """Test creation of input->recipe and recipe->output edges."""
        edges = identifier._extract_graph_edges(mock_project, ["compute_B"])

        # Should have 2 edges: input->recipe, recipe->output
        assert len(edges) == 2

        # Verify input edge
        input_edge = next(e for e in edges if e["target"] == "compute_B")
        assert input_edge["source"] == "input_ds"

        # Verify output edge
        output_edge = next(e for e in edges if e["source"] == "compute_B")
        assert output_edge["target"] == "output_ds"

    def test_handles_multiple_recipes(self, identifier, mock_project):
        """Test edge extraction from multiple recipes."""
        edges = identifier._extract_graph_edges(mock_project, ["recipe1", "recipe2"])

        # Should have edges for both recipes (2 edges each = 4 total)
        assert len(edges) == 4

    def test_handles_recipe_with_multiple_inputs_outputs(self, identifier):
        """Test recipes with multiple inputs and outputs."""
        # Mock recipe with 2 inputs, 2 outputs
        recipe = MagicMock()
        settings = MagicMock()
        settings.get_raw.return_value = {
            "type": "join",
            "inputs": {
                "left": {"ref": "ds_left"},
                "right": {"ref": "ds_right"}
            },
            "outputs": {
                "joined": {"ref": "ds_joined"},
                "rejected": {"ref": "ds_rejected"}
            }
        }
        recipe.get_settings.return_value = settings

        project = Mock()
        project.get_recipe.return_value = recipe

        edges = identifier._extract_graph_edges(project, ["join_recipe"])

        # Should have 4 edges: 2 inputs + 2 outputs
        assert len(edges) == 4

        # Verify inputs
        input_edges = [e for e in edges if e["target"] == "join_recipe"]
        assert len(input_edges) == 2
        assert any(e["source"] == "ds_left" for e in input_edges)
        assert any(e["source"] == "ds_right" for e in input_edges)

        # Verify outputs
        output_edges = [e for e in edges if e["source"] == "join_recipe"]
        assert len(output_edges) == 2
        assert any(e["target"] == "ds_joined" for e in output_edges)
        assert any(e["target"] == "ds_rejected" for e in output_edges)

    def test_handles_api_errors_gracefully(self, identifier):
        """Test graceful handling of recipe API failures."""
        project = Mock()
        project.get_recipe.side_effect = Exception("API error")

        edges = identifier._extract_graph_edges(project, ["bad_recipe"])

        # Should return empty list, not raise exception
        assert edges == []

    def test_continues_after_single_recipe_failure(self, identifier, mock_recipe_with_io):
        """Test that one failed recipe doesn't stop processing."""
        project = Mock()

        def get_recipe_side_effect(name):
            if name == "bad_recipe":
                raise Exception("Failed")
            return mock_recipe_with_io

        project.get_recipe.side_effect = get_recipe_side_effect

        edges = identifier._extract_graph_edges(project, ["bad_recipe", "good_recipe"])

        # Should have edges from good_recipe only
        assert len(edges) == 2
        assert all("good_recipe" in [e["source"], e["target"]] for e in edges)
