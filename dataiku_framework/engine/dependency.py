"""
Dependency resolution for recipes

Determines the correct order to create/execute recipes based on their inputs/outputs.
"""

from typing import List, Dict, Set
from dataiku_framework.config.schema import RecipeConfig


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected"""

    pass


class DependencyResolver:
    """Resolve recipe dependencies using topological sort"""

    @staticmethod
    def resolve(recipes: List[RecipeConfig]) -> List[str]:
        """
        Resolve recipe dependencies and return execution order.

        Uses topological sort (Kahn's algorithm) to determine correct order.

        Args:
            recipes: List of recipe configurations

        Returns:
            List of recipe names in dependency order (can be executed sequentially)

        Raises:
            CircularDependencyError: If circular dependencies detected
        """
        # Build dependency graph
        # graph[recipe_name] = set of recipes that depend on this recipe
        graph: Dict[str, Set[str]] = {}
        in_degree: Dict[str, int] = {}

        # Initialize
        for recipe in recipes:
            graph[recipe.name] = set()
            in_degree[recipe.name] = 0

        # Build graph: if recipe A outputs to dataset X and recipe B uses X as input,
        # then B depends on A (A must run before B)
        output_to_recipe: Dict[str, str] = {}

        # Map outputs to recipes
        for recipe in recipes:
            for output in recipe.outputs:
                output_to_recipe[output] = recipe.name

        # Build dependencies
        for recipe in recipes:
            for input_dataset in recipe.inputs:
                # Check if this input is produced by another recipe
                if input_dataset in output_to_recipe:
                    # recipe depends on the recipe that produces input_dataset
                    producer = output_to_recipe[input_dataset]
                    if producer != recipe.name:  # Avoid self-dependency
                        graph[producer].add(recipe.name)
                        in_degree[recipe.name] += 1

        # Topological sort (Kahn's algorithm)
        queue: List[str] = []
        result: List[str] = []

        # Start with recipes that have no dependencies
        for recipe_name in in_degree:
            if in_degree[recipe_name] == 0:
                queue.append(recipe_name)

        # Process queue
        while queue:
            # Sort for deterministic ordering
            queue.sort()
            current = queue.pop(0)
            result.append(current)

            # Remove edges from current recipe
            for dependent in graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check for circular dependencies
        if len(result) != len(recipes):
            remaining = [r.name for r in recipes if r.name not in result]
            raise CircularDependencyError(
                f"Circular dependency detected in recipes: {', '.join(remaining)}. "
                f"Check that recipes don't have cyclical input/output relationships."
            )

        return result

    @staticmethod
    def validate_no_cycles(recipes: List[RecipeConfig]) -> bool:
        """
        Validate that there are no circular dependencies.

        Args:
            recipes: List of recipe configurations

        Returns:
            True if no cycles, raises exception otherwise

        Raises:
            CircularDependencyError: If circular dependencies detected
        """
        DependencyResolver.resolve(recipes)
        return True

    @staticmethod
    def get_dependencies(
        recipe_name: str, recipes: List[RecipeConfig]
    ) -> List[str]:
        """
        Get all recipes that a given recipe depends on (direct + transitive).

        Args:
            recipe_name: Name of the recipe
            recipes: List of all recipe configurations

        Returns:
            List of recipe names that must run before this recipe
        """
        # Find the recipe
        recipe = next((r for r in recipes if r.name == recipe_name), None)
        if not recipe:
            return []

        # Map outputs to recipes
        output_to_recipe: Dict[str, str] = {}
        for r in recipes:
            for output in r.outputs:
                output_to_recipe[output] = r.name

        # Find direct dependencies
        dependencies: Set[str] = set()
        for input_dataset in recipe.inputs:
            if input_dataset in output_to_recipe:
                producer = output_to_recipe[input_dataset]
                if producer != recipe_name:
                    dependencies.add(producer)

        # Find transitive dependencies (recursive)
        all_deps: Set[str] = set()
        visited: Set[str] = set()

        def find_deps(r_name: str):
            if r_name in visited:
                return
            visited.add(r_name)

            r = next((rec for rec in recipes if rec.name == r_name), None)
            if not r:
                return

            for input_ds in r.inputs:
                if input_ds in output_to_recipe:
                    producer = output_to_recipe[input_ds]
                    if producer != r_name:
                        all_deps.add(producer)
                        find_deps(producer)

        find_deps(recipe_name)
        return sorted(list(all_deps))

    @staticmethod
    def get_execution_groups(recipes: List[RecipeConfig]) -> List[List[str]]:
        """
        Group recipes into execution groups where recipes in the same group
        can be executed in parallel.

        Args:
            recipes: List of recipe configurations

        Returns:
            List of recipe groups (each group can run in parallel)
        """
        # Get dependency order
        ordered = DependencyResolver.resolve(recipes)

        # Map recipe name to its position
        position = {name: i for i, name in enumerate(ordered)}

        # Build dependency map
        output_to_recipe: Dict[str, str] = {}
        for r in recipes:
            for output in r.outputs:
                output_to_recipe[output] = r.name

        # Assign recipes to levels
        levels: Dict[str, int] = {}

        for recipe in recipes:
            # Find max level of dependencies
            max_dep_level = -1
            for input_dataset in recipe.inputs:
                if input_dataset in output_to_recipe:
                    producer = output_to_recipe[input_dataset]
                    if producer != recipe.name and producer in levels:
                        max_dep_level = max(max_dep_level, levels[producer])

            levels[recipe.name] = max_dep_level + 1

        # Group by level
        groups: Dict[int, List[str]] = {}
        for recipe_name, level in levels.items():
            if level not in groups:
                groups[level] = []
            groups[level].append(recipe_name)

        # Return sorted groups
        result = []
        for level in sorted(groups.keys()):
            result.append(sorted(groups[level]))

        return result
