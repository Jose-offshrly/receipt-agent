from typing import Literal
from pydantic import BaseModel, Field


class Category(BaseModel):
    id: int
    category_name: str


class SelectCategory(BaseModel):
    """Categorize receipt accurately and within expected values."""

    category_name: Literal["Healthcare", "Restaurant"] = Field(
        ...,
        description="Given a receipt data choose which category / acount type is accurate for the given receipt which will be use for xero api later",
    )
