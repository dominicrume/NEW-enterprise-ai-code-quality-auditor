"""
Validation and quarantine module for the data pipeline.
Enforces the schema rules and writes invalid rows to the quarantine directory.
"""

import os
import csv
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger("data_pipeline.validate")

# Declared Column Schema
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
    Does not log or include raw row values in error reasons to ensure PII is not leaked.
    Returns:
        A tuple of (is_valid, validated_row_dict, error_reason_string).
    """
    validated = {}
    
    for field, rules in COLUMN_SCHEMA.items():
        val = row.get(field, "").strip()
        is_required = rules["required"]
        field_type = rules["type"]
        
        # Check required fields
        if is_required and not val:
            return False, None, f"Missing required field '{field}'"
            
        if not val:
            # Optional field is empty, save as None
            validated[field] = None
            continue
            
        # Type conversions
        try:
            if field_type == "int":
                # Ensure it's a valid integer
                validated[field] = int(val)
            elif field_type == "float":
                # Ensure it's a valid float
                validated[field] = float(val)
            else:
                # String field
                validated[field] = val
        except ValueError:
            return False, None, f"Invalid type for field '{field}' (expected {field_type})"
            
    return True, validated, None

class QuarantineManager:
    """
    Manages writing quarantined rows to a CSV file.
    Lazily creates the file only when the first invalid row is encountered.
    """
    def __init__(self, quarantine_dir: str, run_id: str):
        self.quarantine_dir = quarantine_dir
        self.run_id = run_id
        self.file_path = os.path.join(
            self.quarantine_dir, 
            f"quarantine_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{self.run_id[:8]}.csv"
        )
        self.file = None
        self.writer = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()
            logger.info(f"Invalid rows written to quarantine file: {self.file_path}")

    def quarantine_row(self, raw_row: Dict[str, str], reason: str):
        """
        Quarantines a row by writing it to the quarantine CSV.
        Creates the file and writes the header if it hasn't been created yet.
        """
        if not self.file:
            # Ensure parent directories exist
            os.makedirs(self.quarantine_dir, exist_ok=True)
            self.file = open(self.file_path, mode="w", newline="", encoding="utf-8")
            
            # The header includes all original keys in the row plus the quarantine reason
            headers = list(raw_row.keys())
            if "quarantine_reason" not in headers:
                headers.append("quarantine_reason")
                
            self.writer = csv.DictWriter(self.file, fieldnames=headers)
            self.writer.writeheader()

        # Prepare the quarantined row copy
        row_copy = dict(raw_row)
        row_copy["quarantine_reason"] = reason
        self.writer.writerow(row_copy)
