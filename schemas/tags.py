from typing import TypedDict


class Tag(TypedDict):
    """One record in the TAGS store."""

    id: int
    name: str
