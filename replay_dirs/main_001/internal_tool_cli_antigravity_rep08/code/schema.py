"""
Schema definitions and validator logic for the ETL pipeline.
"""
from typing import Dict, Any, Tuple, Optional

# Declared Column Schema
# Maps field names to their configuration: type and whether they are required.
# Note: The schema is structured to ensure that no PII is requested, stored, or processed.
COLUMN_SCHEMA = {
    "transaction_id": {"type": "str", "required": True},
    "product_id": {"type": "str", "required": True},
    "price": {"type": "float", "required": True},
    "quantity": {"type": "int", "required": True},
    "category": {"type": "str", "required": False}
}

def validate_row(row: Dict[str, str]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Validates a raw row against the declared COLUMN_SCHEMA.
    
    Args:
        row: A dictionary representing the raw input row (strings from CSV).
        
    Returns:
        A tuple of (is_valid, validated_row, error_reason).
        If is_valid is False, validated_row is None and error_reason is a description of the failure.
    """
    validated = {}
    
    # 1. Check for unexpected extra columns (or mismatch)
    # We do a lenient match but ensure required fields exist and are validated.
    
    for field, rules in COLUMN_SCHEMA.items():
        val = row.get(field, "").strip()
        is_required = rules["required"]
        field_type = rules["type"]
        
        # Check required fields
        if is_required and not val:
            # Governance: Do not include the actual row values in the error reason to prevent logging PII
            return False, None, f"Missing required field '{field}'"
        
        if not val:
            # Optional field is empty, store as None or empty string depending on preference.
            # For category, let's keep it empty or None.
            validated[field] = None
            continue
            
        # Type conversions
        try:
            if field_type == "int":
                # Check that it's a valid integer
                validated[field] = int(val)
            elif field_type == "float":
                # Check that it's a valid float
                validated[field] = float(val)
            else:
                # String type, keep as is
                validated[field] = val
        except ValueError:
            # Governance: Do not include the actual value in the log/error to prevent PII exposure
            return False, None, f"Invalid type for field '{field}' (expected {field_type})"
            
    return True, validated, None
