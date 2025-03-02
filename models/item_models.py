"""
Pydantic models for item analysis in the Vinted Analyzer application.
"""
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ItemDetails(BaseModel):
    """ Pydantic model for storing second-hand item details. """
    model_config = ConfigDict(validate_assignment=True, extra='forbid')

    name: str = Field(..., description="The name/title of the item.")
    category: str = Field(..., description="The category of the product.")
    bargain_potential: int = Field(
        ...,
        ge=0,
        le=10,
        description="A score representing the bargain potential of the item (0-10)."
    )
    condition: Optional[str] = Field(
        None,
        description="A brief description of the condition of the item."
    )


class SellerInfo(BaseModel):
    """Pydantic model for storing seller information."""
    model_config = ConfigDict(validate_assignment=True, extra='forbid')

    seller_name: str = Field(..., description="The name of the seller.")
    reputation: str = Field(..., description="The seller's reputation or rating.")
    items_sold: int = Field(..., description="Number of items the seller has sold.")
    market_presence: int = Field(..., ge=0, le=10,
                                 description="A score representing the seller's market presence (0-10).")

class ItemAnalysisResult(BaseModel):
    """Pydantic model for storing the results of item analysis."""
    model_config = ConfigDict(validate_assignment=True, extra='forbid')

    item_id: str = Field(..., description="The unique identifier of the item.")
    score: int = Field(..., ge=0, le=100, description="The overall score of the item (0-100).")
    notes: str = Field(..., description="Notes explaining the scoring rationale and recommendations.")
    title: str = Field(..., description="The title of the item.")
    price: float = Field(..., description="The price of the item.")
    status: str = Field(..., description="The condition or status of the item.")