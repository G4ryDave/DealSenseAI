"""
Pydantic models for deal message generation and market analysis.
"""
from typing import Optional, List, Tuple

from pydantic import BaseModel, Field, ConfigDict


class MarketConfidenceMetrics(BaseModel):
    """
    Model for market confidence metrics with clear explanations.

    Market confidence represents how reliable the market data is on a scale of 1-10:
    - 10: Extensive data from multiple reliable sources with consistent pricing
    - 7-9: Good data from reliable sources with minor variations
    - 4-6: Limited data or significant price variations
    - 1-3: Very limited data, unreliable sources, or extreme price variations
    """
    model_config = ConfigDict(validate_assignment=True, extra='forbid')

    score: int = Field(
        ...,
        ge=1,
        le=10,
        description="Confidence score (1-10) indicating reliability of market data"
    )
    factors: List[str] = Field(
        ...,
        description="Factors contributing to the confidence score"
    )
    data_sources: int = Field(
        ...,
        description="Number of data sources used for market analysis"
    )
    price_consistency: int = Field(
        ...,
        ge=1,
        le=10,
        description="How consistent prices are across sources (1-10)"
    )

class ItemAnalysisResult(BaseModel):
    """
    Pydantic model for storing the results of item analysis.
    """
    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid',
        json_schema_extra={
            "example": {
                "item_id": "12345",
                "title": "iPhone 13 Pro",
                "price": 699.99,
                "status": "Used - Like New",
                "score": 85,
                "notes": "This iPhone 13 Pro is priced 15% below market average and in excellent condition."
            }
        }
    )

    item_id: str = Field(..., description="The unique identifier of the item.")
    title: str = Field(..., description="The title of the item.")
    price: float = Field(..., description="The current listing price of the item.")
    status: str = Field(..., description="The condition or status of the item (e.g., new, used, like new).")
    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="The overall bargain score of the item (0-100)."
    )
    notes: str = Field(..., description="Notes explaining the scoring rationale and recommendations.")

class MarketResearchResult(BaseModel):
    """
    Model for market research results with detailed pricing information.
    """
    item_id: str = Field(..., description="ID of the item researched")
    average_price: float = Field(..., description="Average market price for similar items")
    price_range: Tuple[float, float] = Field(..., description="Min and max prices found [min, max]")
    comparable_items: List[dict] = Field(
        default_factory=list,
        description="List of comparable items found during research"
    )
    value_assessment: str = Field(
        ...,
        description="Assessment of the item's value compared to market (Underpriced/Fair/Overpriced)"
    )
    market_demand: str = Field(
        ...,
        description="Assessment of market demand (High/Medium/Low)"
    )
    price_factors: List[str] = Field(
        default_factory=list,
        description="Factors affecting the price"
    )
    confidence: MarketConfidenceMetrics = Field(
        ...,
        description="Confidence metrics for the market research"
    )
    notes: Optional[str] = Field(
        None,
        description="Additional notes about the market research"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "item_id": "12345",
                "average_price": 799.99,
                "price_range": [699.99, 899.99],
                "comparable_items": [
                    {"title": "iPhone 13 Pro 128GB", "price": 749.99, "condition": "Used - Good"},
                    {"title": "iPhone 13 Pro 256GB", "price": 849.99, "condition": "Used - Like New"}
                ],
                "value_assessment": "Underpriced",
                "market_demand": "High",
                "price_factors": ["Storage capacity", "Condition", "Included accessories"],
                "confidence": {
                    "score": 8,
                    "factors": ["Multiple reliable sources", "Consistent pricing", "Recent data"],
                    "data_sources": 12,
                    "price_consistency": 7
                },
                "notes": "The iPhone 13 Pro maintains strong resale value with high demand."
            }
        }
    )

class DealMessageResult(BaseModel):
    """
    Model for deal message results with negotiation strategy.
    """
    item_id: str = Field(description="ID of the item the message is for")
    message: str = Field(description="The crafted deal message")
    tone: str = Field(description="Tone of the message (friendly, professional, casual)")
    expected_success_rate: int = Field(
        description="Estimated likelihood of success (0-100) based on current price and offerted price",
        ge=0,
        le=100
    )
    offer_price: Optional[float] = Field(
        None,
        description="Suggested offer price based on market research"
    )
    negotiation_strategy: str = Field(
        description="Brief description of the negotiation strategy used"
    )
    key_points: List[str] = Field(
        default_factory=list,
        description="Key points emphasized in the message"
    )
    market_confidence_assessment: str = Field(
        description="""
        Assessment of market confidence on a scale of 1-10:
        - 10: Extremely confident (extensive reliable data with consistent pricing)
        - 7-9: Very confident (good data from reliable sources with minor variations)
        - 4-6: Moderately confident (limited data or significant price variations)
        - 1-3: Low confidence (very limited data, unreliable sources, or extreme variations)
        """
    )
    notes: Optional[str] = Field(
        None,
        description="Additional notes or recommendations"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "item_id": "12345",
                "message": "Hi there! I'm really interested in your iPhone 13 Pro. It looks to be in great condition! Based on similar phones I've been looking at, would you consider $680? I can pay right away. Thanks for considering!",
                "tone": "friendly",
                "expected_success_rate": 75,
                "offer_price": 680.00,
                "negotiation_strategy": "Friendly approach with justified offer slightly below asking price",
                "key_points": ["Express genuine interest", "Acknowledge condition", "Justify offer", "Offer immediate payment"],
                "market_confidence_assessment": "8/10 - Very confident based on consistent pricing across multiple reliable sources",
                "notes": "A friendly tone works well on Vinted. The offer is 3% below asking but justified by market research."
            }
        }
    )