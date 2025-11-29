"""Custom exceptions for Discovery Agent."""


class DiscoveryError(Exception):
    """
    Base exception for Discovery Agent errors.

    All Discovery Agent specific exceptions inherit from this class.
    """

    pass


class InvalidBlockError(DiscoveryError):
    """
    Raised when a zone is not a valid block.

    This exception is raised when a zone fails block validation,
    such as missing required inputs or outputs.

    Example:
        >>> if not has_outputs(zone):
        >>>     raise InvalidBlockError(
        >>>         f"Zone '{zone.name}' has no outputs"
        >>>     )
    """

    pass


class BlockNotFoundError(DiscoveryError):
    """
    Raised when a requested block cannot be found.

    This exception is raised when attempting to retrieve a block
    from the catalog that doesn't exist.

    Example:
        >>> if block_id not in catalog:
        >>>     raise BlockNotFoundError(
        >>>         f"Block '{block_id}' not found in catalog"
        >>>     )
    """

    pass


class CatalogWriteError(DiscoveryError):
    """
    Raised when writing to the catalog fails.

    This exception is raised when there are errors writing wiki
    articles, updating the JSON index, or storing schemas.

    Example:
        >>> try:
        >>>     write_wiki_article(block)
        >>> except Exception as e:
        >>>     raise CatalogWriteError(
        >>>         f"Failed to write catalog entry: {e}"
        >>>     ) from e
    """

    pass


class SchemaExtractionError(DiscoveryError):
    """
    Raised when schema extraction from a dataset fails.

    This exception is raised when attempting to extract or infer
    a dataset's schema but the operation fails.

    Example:
        >>> try:
        >>>     schema = dataset.get_schema()
        >>> except Exception as e:
        >>>     raise SchemaExtractionError(
        >>>         f"Failed to extract schema from {dataset.name}: {e}"
        >>>     ) from e
    """

    pass
