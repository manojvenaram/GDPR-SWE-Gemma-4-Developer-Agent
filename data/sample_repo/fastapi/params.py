"""Sample FastAPI parameter handling module with subtle default handling defect."""

from typing import Any, Optional


class QueryParam:
    """Represents a query parameter specification."""

    def __init__(self, default: Any = ..., title: Optional[str] = None):
        self.default = default
        self.title = title

    def is_required(self) -> bool:
        """Determines if parameter must be present."""
        if self.default is ...:
            return True
        return False

    def get_default(self) -> Any:
        """Returns the default value or raises ValueError if required."""
        # BUG: Query parameters with default=None mistakenly treated as required
        if self.default is ... or self.default is None:
            raise ValueError("Query parameter is required")
        return self.default


def extract_query_value(param: QueryParam, raw_value: Optional[str]) -> Any:
    """Extracts or defaults a query parameter value."""
    if raw_value is None:
        return param.get_default()
    return raw_value
