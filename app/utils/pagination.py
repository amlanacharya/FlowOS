"""Reusable pagination utilities for database queries."""
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Query
from sqlmodel import Session, select


class PaginationParams:
    """Pagination parameters with safe defaults and bounds."""

    def __init__(self, skip: int = 0, limit: int = 100) -> None:
        """
        Initialize pagination parameters.

        Args:
            skip: Number of records to skip (default: 0, min: 0)
            limit: Number of records to return (default: 100, max: 1000)
        """
        self.skip = max(0, skip)
        self.limit = min(1000, max(1, limit))


def paginate_query(query: Any, skip: int = 0, limit: int = 100) -> Any:
    """
    Apply pagination to a SQLModel query.

    Args:
        query: SQLModel query object
        skip: Number of records to skip
        limit: Number of records to return

    Returns:
        Paginated query
    """
    params = PaginationParams(skip, limit)
    return query.offset(params.skip).limit(params.limit)


async def get_paginated_results(
    session: Session,
    query: Any,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Any], int]:
    """
    Execute paginated query and return results with total count.

    Args:
        session: Database session
        query: SQLModel query
        skip: Number of records to skip
        limit: Number of records to return

    Returns:
        Tuple of (results, total_count)
    """
    # Get total count
    count_query = select(func.count()).select_from(query)
    count_result = await session.execute(count_query)
    total = count_result.scalar() or 0

    # Apply pagination and fetch results
    paginated_query = paginate_query(query, skip, limit)
    result = await session.execute(paginated_query)
    results = result.scalars().all()

    return results, total
