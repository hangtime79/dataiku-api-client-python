"""
Discovery Agent for Dataiku Reusable Workflows.

This package implements the Discovery Agent which crawls Dataiku projects,
identifies reusable blocks (zones), and catalogs them in BLOCKS_REGISTRY.
"""

__version__ = "1.0.0"

from dataikuapi.iac.workflows.discovery.models import (
    BlockMetadata,
    BlockPort,
    BlockContents,
    BlockSummary,
)

from dataikuapi.iac.workflows.discovery.exceptions import (
    DiscoveryError,
    InvalidBlockError,
    BlockNotFoundError,
    CatalogWriteError,
    SchemaExtractionError,
)

__all__ = [
    # Models
    "BlockMetadata",
    "BlockPort",
    "BlockContents",
    "BlockSummary",
    # Exceptions
    "DiscoveryError",
    "InvalidBlockError",
    "BlockNotFoundError",
    "CatalogWriteError",
    "SchemaExtractionError",
]
