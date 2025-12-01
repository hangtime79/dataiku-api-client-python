from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter


class TestGenerateFlowDiagram:
    """Tests for _generate_flow_diagram() method."""

    def test_basic_flow(self):
        """Test basic dataset -> recipe -> dataset flow."""
        writer = CatalogWriter()
        graph = {
            "nodes": [
                {"id": "INPUT", "type": "DATASET"},
                {"id": "transform", "type": "RECIPE"},
                {"id": "OUTPUT", "type": "DATASET"},
            ],
            "edges": [
                {"source": "INPUT", "target": "transform"},
                {"source": "transform", "target": "OUTPUT"},
            ],
        }

        diagram = writer._generate_flow_diagram(graph)

        assert "```mermaid" in diagram
        assert "graph LR" in diagram
        assert "INPUT[INPUT]" in diagram
        assert "transform(transform)" in diagram
        assert "OUTPUT[OUTPUT]" in diagram
        assert "INPUT --> transform" in diagram
        assert "transform --> OUTPUT" in diagram
        assert "```" in diagram

    def test_empty_graph(self):
        """Test empty graph returns empty string."""
        writer = CatalogWriter()
        assert writer._generate_flow_diagram({}) == ""
        assert writer._generate_flow_diagram({"nodes": [], "edges": []}) == ""

    def test_none_graph(self):
        """Test None graph returns empty string."""
        writer = CatalogWriter()
        assert writer._generate_flow_diagram(None) == ""

    def test_sanitizes_ids_with_spaces(self):
        """Test ID sanitization for Mermaid compatibility."""
        writer = CatalogWriter()
        graph = {
            "nodes": [
                {"id": "MY DATASET", "type": "DATASET"},
                {"id": "MY RECIPE", "type": "RECIPE"},
            ],
            "edges": [{"source": "MY DATASET", "target": "MY RECIPE"}],
        }

        diagram = writer._generate_flow_diagram(graph)

        # IDs sanitized in node definitions and edges
        assert "MY_DATASET[MY DATASET]" in diagram
        assert "MY_RECIPE(MY RECIPE)" in diagram
        assert "MY_DATASET --> MY_RECIPE" in diagram
        # Original labels preserved
        assert "MY DATASET" in diagram
        assert "MY RECIPE" in diagram

    def test_multiple_inputs_outputs(self):
        """Test complex pipeline with multiple inputs/outputs."""
        writer = CatalogWriter()
        graph = {
            "nodes": [
                {"id": "INPUT1", "type": "DATASET"},
                {"id": "INPUT2", "type": "DATASET"},
                {"id": "join", "type": "RECIPE"},
                {"id": "OUTPUT1", "type": "DATASET"},
                {"id": "OUTPUT2", "type": "DATASET"},
            ],
            "edges": [
                {"source": "INPUT1", "target": "join"},
                {"source": "INPUT2", "target": "join"},
                {"source": "join", "target": "OUTPUT1"},
                {"source": "join", "target": "OUTPUT2"},
            ],
        }

        diagram = writer._generate_flow_diagram(graph)

        assert "INPUT1 --> join" in diagram
        assert "INPUT2 --> join" in diagram
        assert "join --> OUTPUT1" in diagram
        assert "join --> OUTPUT2" in diagram

    def test_disconnected_nodes(self):
        """Test handling of nodes without edges."""
        writer = CatalogWriter()
        graph = {"nodes": [{"id": "STANDALONE", "type": "DATASET"}], "edges": []}

        diagram = writer._generate_flow_diagram(graph)

        assert "```mermaid" in diagram
        assert "STANDALONE[STANDALONE]" in diagram

    def test_mermaid_structure(self):
        """Test overall Mermaid syntax structure."""
        writer = CatalogWriter()
        graph = {"nodes": [{"id": "DS", "type": "DATASET"}], "edges": []}

        diagram = writer._generate_flow_diagram(graph)
        lines = diagram.strip().split("\n")

        assert lines[0] == "```mermaid"
        assert lines[1] == "graph LR"
        assert lines[-1] == "```"
