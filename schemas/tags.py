from typing import TypedDict

class TagRecord(TypedDict):
    id: int
    name: str

REQUIRED_FIELDS = ("name",)
