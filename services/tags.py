from utils.errors import ValidationError
from schemas.tags import REQUIRED_FIELDS

TAGS: dict[int, dict] = {
    1: {"id": 1, "name": "urgent"},
}

def create_tag(data: dict) -> dict:
    """Create a new tag.

    Args:
        data: The request payload. Must be a JSON object containing all
            fields in REQUIRED_FIELDS.

    Returns:
        The newly created tag record.

    Raises:
        ValidationError: If data is not a JSON object or is missing a
            required field.
    """
    if not isinstance(data, dict):
        raise ValidationError("body", "must be a JSON object")
    for field in REQUIRED_FIELDS:
        if field not in data:
            raise ValidationError(field, "is required")
    new_id = max(TAGS.keys(), default=0) + 1
    TAGS[new_id] = {"id": new_id, "name": data["name"]}
    return TAGS[new_id]
