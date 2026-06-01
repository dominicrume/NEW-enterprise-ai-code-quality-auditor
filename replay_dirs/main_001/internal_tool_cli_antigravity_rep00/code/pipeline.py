"""
Core ETL pipeline implementation.
"""
import os
import csv
import json
import uuid
import time
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

from schema import validate_row

# Set up logging - Ensure we do not log PII (No raw values, only counts/types/field names)
logger = logging.getLogger("data_pipeline")

class DataPipeline:
    def __init__(self, input_dir: str, db_path: str, quarantine_dir: str, summary_dir: str):
        self.input_dir = input_dir
        self.db_path = db_path
        self.quarantine_dir = quarantine_dir
        self.summary_dir = summary_dir
        
        # Ensure directories exist
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.quarantine_dir, exist_ok=True)
        os.makedirs(self.summary_dir, exist_ok=True)
        
        # Initialize SQLite database
        self._init_db()

    def _init_db(self):
        """Initializes the SQLite database and ensures the schema is set up."""
        logger.info(f"Initializing SQLite database at {self.db_path}")
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            # transaction_id is PRIMARY KEY to enforce row-level idempotency
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    product_id TEXT,
                    price REAL,
                    quantity INTEGER,
                    category TEXT,
                    processed_at TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def run(self) -> Dict[str, Any]:
        """Runs the ETL pipeline on all CSV files in the input directory."""
        run_id = str(uuid.uuid4())
        start_time = time.time()
        start_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        logger.info(f"Starting run {run_id} at {start_timestamp}")
        
        total_rows = 0
        valid_rows_count = 0
        quarantine_rows_count = 0
        loaded_rows_count = 0
        
        # Find all CSV files in the input directory
        csv_files = [f for f in os.listdir(self.input_dir) if f.lower().endswith(".csv")]
        
        # Prepare quarantine file for this run
        quarantine_file_path = os.path.join(
            self.quarantine_dir, f"quarantine_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{run_id[:8]}.csv"
        )
        
        quarantine_writer = None
        quarantine_file = None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for csv_filename in csv_files:
                file_path = os.path.join(self.input_dir, csv_filename)
                logger.info(f"Ingesting file: {csv_filename}")
                
                with open(file_path, mode="r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    
                    # Clean headers to strip spaces or byte order marks
                    reader.fieldnames = [name.strip() for name in reader.fieldnames] if reader.fieldnames else []
                    
                    for raw_row in reader:
                        total_rows += 1
                        
                        # Validate the row against schema
                        is_valid, validated_row, error_reason = validate_row(raw_row)
                        
                        if not is_valid:
                            quarantine_rows_count += 1
                            # Open quarantine file lazily
                            if quarantine_file is None:
                                quarantine_file = open(quarantine_file_path, mode="w", newline="", encoding="utf-8")
                                # Write raw row headers plus error reason
                                fieldnames = list(raw_row.keys()) + ["quarantine_reason"]
                                quarantine_writer = csv.DictWriter(quarantine_file, fieldnames=fieldnames)
                                quarantine_writer.writeheader()
                            
                            # Add error reason and write to quarantine (Governance: No PII logging on stdout/logs)
                            quarantine_row = dict(raw_row)
                            quarantine_row["quarantine_reason"] = error_reason
                            quarantine_writer.writerow(quarantine_row)
                            continue
                        
                        # Transform / Normalise
                        # 1. Lowercase string columns (product_id, category if present)
                        if validated_row["product_id"]:
                            validated_row["product_id"] = validated_row["product_id"].lower()
                        if validated_row["category"]:
                            validated_row["category"] = validated_row["category"].lower()
                            
                        # 2. Round numeric columns to two decimal places
                        validated_row["price"] = round(validated_row["price"], 2)
                        
                        valid_rows_count += 1
                        
                        # Load: Write to SQLite with INSERT OR IGNORE for idempotency
                        processed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                        cursor.execute("""
                            INSERT OR IGNORE INTO transactions (
                                transaction_id, product_id, price, quantity, category, processed_at
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            validated_row["transaction_id"],
                            validated_row["product_id"],
                            validated_row["price"],
                            validated_row["quantity"],
                            validated_row["category"],
                            processed_at
                        ))
                        
                        if cursor.rowcount > 0:
                            loaded_rows_count += 1
            
            conn.commit()
            status = "SUCCESS"
        except Exception as e:
            conn.rollback()
            status = "FAILED"
            logger.error(f"Pipeline execution failed: {str(e)}") # Generic exception logging, no PII
            raise e
        finally:
            conn.close()
            if quarantine_file is not None:
                quarantine_file.close()
                logger.info(f"Invalid rows written to quarantine file: {quarantine_file_path}")
        
        end_time = time.time()
        duration = end_time - start_time
        end_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Write JSON Summary
        summary = {
            "run_id": run_id,
            "start_time": start_timestamp,
            "end_time": end_timestamp,
            "duration_seconds": round(duration, 4),
            "total_rows_read": total_rows,
            "valid_rows_processed": valid_rows_count,
            "quarantined_rows_count": quarantine_rows_count,
            "inserted_rows_count": loaded_rows_count,
            "status": status
        }
        
        summary_file_path = os.path.join(self.summary_dir, f"summary_{run_id}.json")
        with open(summary_file_path, mode="w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
            
        logger.info(f"Run summary written to {summary_file_path}")
        return summary
