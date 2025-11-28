"""Catalog Writer for Discovery Agent.

This module implements the CatalogWriter class which writes block metadata
to the catalog including wiki articles, JSON index, and schema files.
"""

from typing import Dict, List, Any, Optional
import json
import re
from dataikuapi.iac.workflows.discovery.models import BlockMetadata, BlockSummary
from dataikuapi.iac.workflows.discovery.exceptions import CatalogWriteError


class CatalogWriter:
    """
    Writes block metadata to the catalog.

    The CatalogWriter implements Algorithm 5 (Wiki Article Generation) and
    handles writing blocks to the BLOCKS_REGISTRY catalog including:
    - Wiki articles with metadata
    - JSON catalog index
    - Schema files

    Example:
        >>> writer = CatalogWriter()
        >>> article = writer.generate_wiki_article(block_metadata)
        >>> print(article[:100])
    """

    def __init__(self):
        """Initialize CatalogWriter."""
        pass

    def generate_wiki_article(self, metadata: BlockMetadata) -> str:
        """
        Generate wiki article from block metadata.

        Implements Algorithm 5 from the specification:
        - YAML frontmatter with metadata
        - Title and description
        - Inputs and outputs tables
        - Contains section
        - Dependencies section
        - Usage example
        - Changelog

        Args:
            metadata: BlockMetadata object

        Returns:
            Markdown string for wiki article

        Example:
            >>> article = writer.generate_wiki_article(metadata)
            >>> print("---" in article)  # Has frontmatter
            True
        """
        if metadata is None:
            raise CatalogWriteError("Cannot generate article from None metadata")

        sections = []

        # 1. YAML Frontmatter
        sections.append(self._generate_frontmatter(metadata))

        # 2. Title
        title = metadata.name or metadata.block_id
        sections.append(f"# {title}")
        sections.append("")

        # 3. Description
        sections.append("## Description")
        sections.append("")
        description = metadata.description or "No description provided."
        sections.append(description)
        sections.append("")

        # 4. Inputs Table
        if metadata.inputs:
            sections.append("## Inputs")
            sections.append("")
            sections.append("| Name | Type | Required | Description |")
            sections.append("|------|------|----------|-------------|")
            for inp in metadata.inputs:
                required = "Yes" if inp.required else "No"
                desc = inp.description or ""
                sections.append(f"| {inp.name} | {inp.type} | {required} | {desc} |")
            sections.append("")

        # 5. Outputs Table
        if metadata.outputs:
            sections.append("## Outputs")
            sections.append("")
            sections.append("| Name | Type | Description |")
            sections.append("|------|------|-------------|")
            for out in metadata.outputs:
                desc = out.description or ""
                sections.append(f"| {out.name} | {out.type} | {desc} |")
            sections.append("")

        # 6. Contains Section
        sections.append("## Contains")
        sections.append("")
        if metadata.contains.datasets:
            datasets_list = ", ".join(metadata.contains.datasets)
            sections.append(f"**Datasets:** {datasets_list}")
            sections.append("")
        if metadata.contains.recipes:
            recipes_list = ", ".join(metadata.contains.recipes)
            sections.append(f"**Recipes:** {recipes_list}")
            sections.append("")
        if metadata.contains.models:
            models_list = ", ".join(metadata.contains.models)
            sections.append(f"**Models:** {models_list}")
            sections.append("")

        # 7. Dependencies Section
        if metadata.dependencies:
            sections.append("## Dependencies")
            sections.append("")
            if metadata.dependencies.get("python"):
                python_deps = ", ".join(metadata.dependencies["python"])
                sections.append(f"- **Python:** {python_deps}")
                sections.append("")
            if metadata.dependencies.get("plugins"):
                plugin_deps = ", ".join(metadata.dependencies["plugins"])
                sections.append(f"- **Plugins:** {plugin_deps}")
                sections.append("")

        # 8. Usage Example
        sections.append("## Usage")
        sections.append("")
        sections.append("```yaml")
        sections.append("blocks:")
        sections.append(
            f'  - ref: "BLOCKS_REGISTRY/{metadata.block_id}@{metadata.version}"'
        )
        if metadata.inputs:
            sections.append("    inputs:")
            first_input = metadata.inputs[0]
            sections.append(f"      {first_input.name}: your_dataset")
        if metadata.outputs:
            sections.append("    outputs:")
            first_output = metadata.outputs[0]
            sections.append(f"      {first_output.name}: your_output")
        sections.append("```")
        sections.append("")

        # 9. Changelog
        sections.append("## Changelog")
        sections.append("")
        sections.append(f"- {metadata.version}: Initial release")
        sections.append("")

        return "\n".join(sections)

    def _generate_frontmatter(self, metadata: BlockMetadata) -> str:
        """
        Generate YAML frontmatter for wiki article.

        Args:
            metadata: BlockMetadata object

        Returns:
            YAML frontmatter string
        """
        frontmatter = ["---"]
        frontmatter.append(f"block_id: {metadata.block_id}")
        frontmatter.append(f"version: {metadata.version}")
        frontmatter.append(f"type: {metadata.type}")
        frontmatter.append(f"blocked: {metadata.blocked}")
        frontmatter.append(f"source_project: {metadata.source_project}")
        if metadata.source_zone:
            frontmatter.append(f"source_zone: {metadata.source_zone}")
        if metadata.hierarchy_level:
            frontmatter.append(f"hierarchy_level: {metadata.hierarchy_level}")
        if metadata.domain:
            frontmatter.append(f"domain: {metadata.domain}")
        if metadata.tags:
            tags_yaml = json.dumps(metadata.tags)
            frontmatter.append(f"tags: {tags_yaml}")
        frontmatter.append("---")
        frontmatter.append("")

        return "\n".join(frontmatter)

    def generate_block_summary(self, metadata: BlockMetadata) -> str:
        """
        Generate block summary JSON for catalog index.

        Args:
            metadata: BlockMetadata object

        Returns:
            JSON string with block summary
        """
        summary = BlockSummary.from_metadata(metadata)
        return json.dumps(summary.to_dict(), indent=2)

    def merge_catalog_index(
        self, existing_index: Dict[str, Any], metadata: BlockMetadata
    ) -> Dict[str, Any]:
        """
        Merge block into catalog index.

        Adds new block or updates existing block in the index.

        Args:
            existing_index: Existing catalog index dict
            metadata: BlockMetadata to merge

        Returns:
            Updated catalog index dict

        Example:
            >>> index = {"blocks": []}
            >>> updated = writer.merge_catalog_index(index, metadata)
            >>> len(updated["blocks"])
            1
        """
        # Ensure blocks list exists
        if "blocks" not in existing_index:
            existing_index["blocks"] = []

        # Create summary for this block
        summary = BlockSummary.from_metadata(metadata)
        summary_dict = summary.to_dict()

        # Check if block already exists
        found = False
        for i, block in enumerate(existing_index["blocks"]):
            if block.get("block_id") == metadata.block_id:
                # Update existing block
                existing_index["blocks"][i] = summary_dict
                found = True
                break

        # Add new block if not found
        if not found:
            existing_index["blocks"].append(summary_dict)

        return existing_index

    def generate_schema_file(self, schema: Dict[str, Any]) -> str:
        """
        Generate schema file content.

        Args:
            schema: Schema dict

        Returns:
            JSON string with pretty-printed schema
        """
        return json.dumps(schema, indent=2)

    def extract_changelog(self, existing_article: str) -> str:
        """
        Extract changelog section from existing wiki article.

        Args:
            existing_article: Existing article markdown

        Returns:
            Changelog section content or empty string
        """
        # Find changelog section
        changelog_pattern = r"## Changelog\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(changelog_pattern, existing_article, re.DOTALL)

        if match:
            return match.group(1).strip()

        return ""

    def merge_wiki_article(self, existing_article: str, metadata: BlockMetadata) -> str:
        """
        Merge new metadata with existing wiki article.

        Preserves manual edits like changelog while updating metadata.

        Args:
            existing_article: Existing article markdown
            metadata: New BlockMetadata

        Returns:
            Merged article markdown

        Example:
            >>> merged = writer.merge_wiki_article(existing, new_metadata)
            >>> "1.0.0: Initial release" in merged  # Preserves old changelog
            True
        """
        # Extract changelog from existing article
        old_changelog = self.extract_changelog(existing_article)

        # Generate new article
        new_article = self.generate_wiki_article(metadata)

        # If we have old changelog, append it to new article
        if old_changelog:
            # Replace the default changelog with merged version
            new_changelog_line = f"- {metadata.version}: Initial release"

            # Build merged changelog
            merged_changelog = f"- {metadata.version}: Updated\n{old_changelog}"

            # Replace in article
            new_article = new_article.replace(new_changelog_line, merged_changelog)

        return new_article

    def get_wiki_path(self, metadata: BlockMetadata) -> str:
        """
        Get wiki path for block based on hierarchy.

        Organizes blocks by hierarchy level in wiki structure.

        Args:
            metadata: BlockMetadata object

        Returns:
            Wiki path string

        Example:
            >>> path = writer.get_wiki_path(metadata)
            >>> "process" in path  # If hierarchy_level is "process"
            True
        """
        # Base path
        base = "BLOCKS_REGISTRY"

        # Organize by hierarchy if available
        if metadata.hierarchy_level:
            path = f"{base}/{metadata.hierarchy_level}/{metadata.block_id}"
        else:
            path = f"{base}/other/{metadata.block_id}"

        return path
