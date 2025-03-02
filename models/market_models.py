from typing import List

from pydantic import BaseModel, Field, ConfigDict


# Base model with strict configuration for VertexAI compatibility.
class VertexAIModel(BaseModel):
    model_config = ConfigDict(validate_assignment=True, extra='forbid')

    @classmethod
    def schema(cls, by_alias: bool = True, ref_template: str = "#/definitions/{model}") -> dict:
        schema = super().schema(by_alias=by_alias, ref_template=ref_template)

        # Recursively remove any "default" entries from the schema.
        def remove_default(obj):
            if isinstance(obj, dict):
                obj.pop("default", None)
                # Ensure that additionalProperties is set to False for all nested objects
                if "additionalProperties" in obj:
                    obj["additionalProperties"] = False
                for key, value in obj.items():
                    remove_default(value)
            elif isinstance(obj, list):
                for item in obj:
                    remove_default(item)

        remove_default(schema)
        return schema


# Updated ComparableItem now includes required properties to ensure a non-empty JSON schema.
class ComparableItem(VertexAIModel):
    model_config = ConfigDict(validate_assignment=True, extra='forbid')

    source: str = Field(..., description="Source marketplace for the comparable item")
    price: float = Field(..., description="Listed price of the comparable item")
    condition: str = Field(..., description="Condition rating of the comparable item")


# MarketValueResult now uses the updated ComparableItem definition.
class MarketValueResult(VertexAIModel):
    item_id: str = Field(..., description="Unique identifier for the item")
    average_price: float = Field(..., description="Average market price")
    price_range: List[float] = Field(..., description="Price range as [min, max]")
    comparable_items: List[ComparableItem] = Field(
        ...,
        description="List of comparable items with details"
    )
    value_assessment: str = Field(..., description="Assessment of the item's value")
    market_demand: str = Field(..., description="Market demand analysis")
    price_factors: List[str] = Field(..., description="Factors influencing price")
    confidence_score: int = Field(..., ge=0, le=10, description="Confidence score for the assessment")
    notes: str = Field(..., description="Additional notes on the assessment")