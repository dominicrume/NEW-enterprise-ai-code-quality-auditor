"""
Transformation and normalisation module for the data pipeline.
Lowercases text fields (product_id, category) and rounds numeric values (price) to 2 decimal places.
"""

from typing import Dict, Any

def normalise_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalises the validated fields in a row.
    - Lowercases product_id and category if they are present.
    - Rounds price to 2 decimal places.
    """
    normalised = dict(row)
    
    # 1. Lowercase string fields (excluding transaction_id to preserve its unique key format)
    if normalised.get("product_id") is not None:
        normalised["product_id"] = str(normalised["product_id"]).lower()
        
    if normalised.get("category") is not None:
        normalised["category"] = str(normalised["category"]).lower()
        
    # 2. Round float fields to 2 decimal places
    if normalised.get("price") is not None:
        normalised["price"] = round(float(normalised["price"]), 2)
        
    return normalised
