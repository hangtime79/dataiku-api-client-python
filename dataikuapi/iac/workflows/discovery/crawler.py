"""Flow Crawler for Discovery Agent.

This module implements the FlowCrawler class which traverses Dataiku project flows,
analyzes zone boundaries, and builds dependency graphs for block identification.
"""

from typing import Dict, List, Any, Set, Optional
from dataikuapi import DSSClient


class FlowCrawler:
    """
    Crawls Dataiku project flows to identify zones and their boundaries.

    The FlowCrawler traverses project flows, analyzes zone membership of datasets
    and recipes, and identifies zone boundaries (inputs, outputs, internals) for
    block identification.

    Attributes:
        client: DSSClient instance for API access

    Example:
        >>> client = DSSClient(host, api_key)
        >>> crawler = FlowCrawler(client)
        >>> zones = crawler.list_zones("MY_PROJECT")
        >>> boundary = crawler.analyze_zone_boundary("MY_PROJECT", "processing_zone")
    """

    def __init__(self, client: DSSClient):
        """
        Initialize FlowCrawler with DSSClient.

        Args:
            client: Authenticated DSSClient instance
        """
        self.client = client

    def get_project_flow(self, project_key: str) -> Any:
        """
        Get the flow object for a project.

        Args:
            project_key: Project identifier

        Returns:
            DSSProjectFlow object

        Raises:
            Exception: If project not found or flow cannot be accessed
        """
        project = self.client.get_project(project_key)
        return project.get_flow()

    def list_zones(self, project_key: str) -> List[str]:
        """
        List all zones in a project.

        Args:
            project_key: Project identifier

        Returns:
            List of zone names

        Example:
            >>> crawler.list_zones("MY_PROJECT")
            ['ingestion', 'processing', 'output']
        """
        flow = self.get_project_flow(project_key)
        zones_data = flow.list_zones()

        # Extract zone IDs from zones data
        # In real Dataiku API, zones have .id and .name attributes
        zone_ids = []
        for zone in zones_data:
            if isinstance(zone, dict) and "name" in zone:
                # Mock format: dict with "name" key
                zone_ids.append(zone["name"])
            elif hasattr(zone, "id"):
                # Real Dataiku format: DSSFlowZone object with .id attribute
                zone_ids.append(zone.id)
            elif hasattr(zone, "name"):
                # Fallback to name if no id
                zone_ids.append(zone.name)
            elif isinstance(zone, str):
                # Zone identifier already a string
                zone_ids.append(zone)

        return zone_ids

    def get_zone_items(self, project_key: str, zone_name: str) -> Dict[str, List[str]]:
        """
        Get all datasets and recipes in a specific zone.

        Args:
            project_key: Project identifier
            zone_name: Zone identifier (can be zone ID or name)

        Returns:
            Dictionary with 'datasets' and 'recipes' keys containing lists of names

        Example:
            >>> items = crawler.get_zone_items("MY_PROJECT", "processing")
            >>> print(items)
            {
                'datasets': ['raw_data', 'processed_data'],
                'recipes': ['clean_data', 'transform_data']
            }
        """
        flow = self.get_project_flow(project_key)
        zone = flow.get_zone(zone_name)  # zone_name can be zone ID or name

        datasets = []
        recipes = []

        # Get zone items from zone object
        if hasattr(zone, "items"):
            for item in zone.items:
                if isinstance(item, dict):
                    item_type = item.get("type", "").lower()
                    item_id = item.get("id", "")
                    if "dataset" in item_type:
                        datasets.append(item_id)
                    elif "recipe" in item_type:
                        recipes.append(item_id)

        return {"datasets": datasets, "recipes": recipes}

    def build_dependency_graph(self, project_key: str) -> Dict[str, Any]:
        """
        Build a dependency graph for the entire project flow.

        Constructs a graph representation with nodes (datasets/recipes) and
        edges (dependencies between them).

        Args:
            project_key: Project identifier

        Returns:
            Dictionary with 'nodes' and 'edges' keys

        Example:
            >>> graph = crawler.build_dependency_graph("MY_PROJECT")
            >>> print(graph)
            {
                'nodes': [
                    {'id': 'dataset1', 'type': 'dataset'},
                    {'id': 'recipe1', 'type': 'recipe'}
                ],
                'edges': [
                    {'from': 'dataset1', 'to': 'recipe1'}
                ]
            }
        """
        flow = self.get_project_flow(project_key)
        graph_data = flow.get_graph()

        nodes = []
        edges = []

        # Process graph data
        if isinstance(graph_data, dict):
            # Handle dict-style graph
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])
        elif hasattr(graph_data, "nodes") and hasattr(graph_data, "edges"):
            # Handle object-style graph
            nodes = graph_data.nodes
            edges = graph_data.edges

        return {"nodes": nodes, "edges": edges}

    def get_dataset_upstream(self, project_key: str, dataset_name: str) -> List[str]:
        """
        Get list of recipes that produce (are upstream of) a dataset.

        Args:
            project_key: Project identifier
            dataset_name: Dataset name

        Returns:
            List of recipe names that produce this dataset

        Example:
            >>> upstream = crawler.get_dataset_upstream("MY_PROJECT", "processed_data")
            >>> print(upstream)
            ['clean_recipe', 'transform_recipe']
        """
        graph = self.build_dependency_graph(project_key)
        upstream_recipes = []

        # Find edges pointing to this dataset
        for edge in graph.get("edges", []):
            if isinstance(edge, dict):
                target = edge.get("to") or edge.get("target")
                source = edge.get("from") or edge.get("source")

                if target == dataset_name:
                    # Check if source is a recipe
                    for node in graph.get("nodes", []):
                        if isinstance(node, dict):
                            node_id = node.get("id")
                            node_type = node.get("type", "").lower()
                            if node_id == source and "recipe" in node_type:
                                upstream_recipes.append(source)

        return upstream_recipes

    def get_dataset_downstream(self, project_key: str, dataset_name: str) -> List[str]:
        """
        Get list of recipes that consume (are downstream of) a dataset.

        Args:
            project_key: Project identifier
            dataset_name: Dataset name

        Returns:
            List of recipe names that consume this dataset

        Example:
            >>> downstream = crawler.get_dataset_downstream("MY_PROJECT", "raw_data")
            >>> print(downstream)
            ['clean_recipe']
        """
        graph = self.build_dependency_graph(project_key)
        downstream_recipes = []

        # Find edges starting from this dataset
        for edge in graph.get("edges", []):
            if isinstance(edge, dict):
                source = edge.get("from") or edge.get("source")
                target = edge.get("to") or edge.get("target")

                if source == dataset_name:
                    # Check if target is a recipe
                    for node in graph.get("nodes", []):
                        if isinstance(node, dict):
                            node_id = node.get("id")
                            node_type = node.get("type", "").lower()
                            if node_id == target and "recipe" in node_type:
                                downstream_recipes.append(target)

        return downstream_recipes

    def analyze_zone_boundary(self, project_key: str, zone_name: str) -> Dict[str, Any]:
        """
        Analyze zone boundary to identify inputs, outputs, and internals.

        Implements Algorithm 1 from the specification:
        - Inputs: Datasets with no upstream recipes in zone
        - Outputs: Datasets consumed by recipes outside zone
        - Internals: Datasets fully contained within zone
        - Validates containment for block validity

        Args:
            project_key: Project identifier
            zone_name: Zone name to analyze

        Returns:
            Dictionary with:
            - inputs: List of input dataset names
            - outputs: List of output dataset names
            - internals: List of internal dataset names
            - is_valid: Boolean indicating if zone forms valid block

        Example:
            >>> boundary = crawler.analyze_zone_boundary("MY_PROJECT", "processing")
            >>> print(boundary)
            {
                'inputs': ['raw_data'],
                'outputs': ['processed_data'],
                'internals': ['temp_data'],
                'is_valid': True
            }
        """
        # Get zone items
        zone_items = self.get_zone_items(project_key, zone_name)
        zone_datasets = set(zone_items["datasets"])
        zone_recipes = set(zone_items["recipes"])

        inputs: Set[str] = set()
        outputs: Set[str] = set()
        internals: Set[str] = set()

        # Analyze each dataset in the zone
        for dataset in zone_datasets:
            upstream = set(self.get_dataset_upstream(project_key, dataset))
            downstream = set(self.get_dataset_downstream(project_key, dataset))

            # Check if upstream recipes are in zone
            upstream_in_zone = upstream & zone_recipes
            has_upstream_outside = bool(upstream - zone_recipes)

            # Check if downstream recipes are in zone
            downstream_in_zone = downstream & zone_recipes
            has_downstream_outside = bool(downstream - zone_recipes)

            # Classify dataset
            if not upstream_in_zone or has_upstream_outside:
                # No upstream in zone, or has upstream outside → input
                inputs.add(dataset)
            elif has_downstream_outside:
                # Has downstream outside → output
                outputs.add(dataset)
            elif upstream_in_zone and downstream_in_zone:
                # Fully contained → internal
                internals.add(dataset)

        # Validate containment
        is_valid = self._validate_containment(
            project_key, zone_recipes, inputs, outputs, internals
        )

        return {
            "inputs": sorted(list(inputs)),
            "outputs": sorted(list(outputs)),
            "internals": sorted(list(internals)),
            "is_valid": is_valid,
        }

    def _validate_containment(
        self,
        project_key: str,
        zone_recipes: Set[str],
        inputs: Set[str],
        outputs: Set[str],
        internals: Set[str],
    ) -> bool:
        """
        Validate that all recipe inputs/outputs are within zone boundary.

        Args:
            project_key: Project identifier
            zone_recipes: Set of recipe names in zone
            inputs: Set of input dataset names
            outputs: Set of output dataset names
            internals: Set of internal dataset names

        Returns:
            True if zone forms valid block, False otherwise
        """
        valid_datasets = inputs | outputs | internals
        graph = self.build_dependency_graph(project_key)

        # Check each recipe in the zone
        for recipe in zone_recipes:
            # Find recipe's input and output datasets
            recipe_inputs = self._get_recipe_inputs(graph, recipe)
            recipe_outputs = self._get_recipe_outputs(graph, recipe)

            # All recipe inputs must be in valid_datasets
            if not set(recipe_inputs).issubset(valid_datasets):
                return False

            # All recipe outputs must be in valid_datasets
            if not set(recipe_outputs).issubset(valid_datasets):
                return False

        return True

    def _get_recipe_inputs(self, graph: Dict[str, Any], recipe_name: str) -> List[str]:
        """
        Get input datasets for a recipe from the graph.

        Args:
            graph: Dependency graph
            recipe_name: Recipe name

        Returns:
            List of input dataset names
        """
        inputs = []

        for edge in graph.get("edges", []):
            if isinstance(edge, dict):
                source = edge.get("from") or edge.get("source")
                target = edge.get("to") or edge.get("target")

                if target == recipe_name:
                    # Source is an input to this recipe
                    inputs.append(source)

        return inputs

    def _get_recipe_outputs(self, graph: Dict[str, Any], recipe_name: str) -> List[str]:
        """
        Get output datasets for a recipe from the graph.

        Args:
            graph: Dependency graph
            recipe_name: Recipe name

        Returns:
            List of output dataset names
        """
        outputs = []

        for edge in graph.get("edges", []):
            if isinstance(edge, dict):
                source = edge.get("from") or edge.get("source")
                target = edge.get("to") or edge.get("target")

                if source == recipe_name:
                    # Target is an output of this recipe
                    outputs.append(target)

        return outputs
