"""
Ingestion module for the data pipeline.
Handles file scanning, file SHA-256 hashing, and CSV reading.
"""

import os
import csv
import hashlib
import logging
from typing import List, Dict

logger = logging.getLogger("data_pipeline.ingest")

def list_csv_files(input_dir: str) -> List[str]:
    """
    Scans the given directory and returns a sorted list of CSV file names.
    """
    if not os.path.exists(input_dir):
        logger.warning(f"Input directory '{input_dir}' does not exist.")
        return []
    
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(".csv")]
    return sorted(files)

def get_file_hash(file_path: str) -> str:
    """
    Calculates the SHA-256 hash of a file's content.
    Used for verifying file-level idempotency.
    """
    sha256 = hashlib.sha256()
    # Read in binary chunks to prevent loading huge files into memory and handle all file encodings
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(65536) # 64kb chunks
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()

def read_csv_rows(file_path: str) -> List[Dict[str, str]]:
    """
    Reads a CSV file and returns its rows as a list of dictionaries.
    Strips whitespace from both keys (headers) and values.
    Uses utf-8-sig to handle byte order marks gracefully.
    """
    rows = []
    with open(file_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        
        # Strip header names
        if reader.fieldnames:
            reader.fieldnames = [name.strip() for name in reader.fieldnames if name]
        else:
            return []
            
        for row in reader:
            # Clean values: strip spaces and ignore empty/None keys
            cleaned_row = {}
            for k, v in row.items():
                if k:  # only if key is not None or empty
                    cleaned_row[k] = v.strip() if v else ""
            rows.append(cleaned_row)
            
    return rows
