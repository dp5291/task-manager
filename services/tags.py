from schemas.tags import Tag
from utils.errors import ValidationError

TAGS: dict[int, Tag] = {}

def create_tag(name: str) -> Tag:
    """Create a new tag.

    Args:
        name: The tag's name; surrounding whitespace is stripped.

    Returns:
        The newly created tag record.

    Raises:
        ValidationError: If name is not a string, is empty, or matches an
            existing tag's name (case-insensitive).
    """
    if not isinstance(name, str):
        raise ValidationError("name", "must be a string")
    name = name.strip()
    if not name:
        raise ValidationError("name", "cannot be empty")
    if any(tag["name"].lower() == name.lower() for tag in TAGS.values()):
        raise ValidationError("name", "already exists")
    new_id = max(TAGS.keys(), default=0) + 1
    TAGS[new_id] = {"id": new_id, "name": name}
    return TAGS[new_id]
