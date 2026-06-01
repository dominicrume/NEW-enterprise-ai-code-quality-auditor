"""
Data Pipeline package initializer.
Exposes the core DataPipeline orchestrator.
"""

import os
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from pipeline.ingest import list_csv_files, get_file_hash, read_csv_rows
from pipeline.validate import validate_row, QuarantineManager
from pipeline.transform import normalise_row
from pipeline.load import DatabaseManager
from pipeline.report import write_summary

logger = logging.getLogger("data_pipeline")

class DataPipeline:
    """
    Orchestrator class for running the ingest, validate, transform, and load data pipeline.
    """
    def __init__(self, input_dir: str, db_path: str, quarantine_dir: str, summary_dir: str):
        self.input_dir = input_dir
        self.db_path = db_path
        self.quarantine_dir = quarantine_dir
        self.summary_dir = summary_dir

        # Ensure required directories exist
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.quarantine_dir, exist_ok=True)
        os.makedirs(self.summary_dir, exist_ok=True)

        self.db_manager = DatabaseManager(self.db_path)

    def run(self) -> Dict[str, Any]:
        """
        Executes the ETL pipeline run.
        Returns:
            A dictionary containing the run execution summary.
        """
        run_id = str(uuid.uuid4())
        start_time = time.time()
        start_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        logger.info(f"Starting pipeline run: {run_id}")

        # Initialize the database schemas
        self.db_manager.initialize_schema()

        # Ingest: list all files
        csv_files = list_csv_files(self.input_dir)
        logger.info(f"Found {len(csv_files)} CSV file(s) for ingestion.")

        total_rows_read = 0
        valid_rows_processed = 0
        quarantined_rows_count = 0
        inserted_rows_count = 0
        processed_files_list = []

        # We execute in a single db connection context for performance
        with self.db_manager.connect() as conn:
            for file_name in csv_files:
                file_path = os.path.join(self.input_dir, file_name)
                
                # Check for file-level idempotency
                try:
                    file_hash = get_file_hash(file_path)
                except Exception as e:
                    logger.error(f"Failed to calculate hash for file {file_name}. Skipping. Details: {str(e)}")
                    continue

                if self.db_manager.is_file_processed(conn, file_hash):
                    logger.info(f"File {file_name} has already been processed (hash match). Skipping.")
                    continue

                logger.info(f"Processing file: {file_name}")
                processed_files_list.append(file_name)

                # Initialize quarantine manager lazily for this run
                with QuarantineManager(self.quarantine_dir, run_id) as quarantine:
                    try:
                        rows = read_csv_rows(file_path)
                    except Exception as e:
                        logger.error(f"Error reading CSV file {file_name}: {str(e)}")
                        continue

                    for raw_row in rows:
                        total_rows_read += 1
                        
                        # Validate row
                        is_valid, validated_row, error_reason = validate_row(raw_row)
                        
                        if not is_valid:
                            quarantined_rows_count += 1
                            quarantine.quarantine_row(raw_row, error_reason)
                            continue

                        # Transform / Normalise row
                        normalised = normalise_row(validated_row)
                        valid_rows_processed += 1

                        # Load row into SQLite (row-level idempotency handled via INSERT OR IGNORE)
                        inserted = self.db_manager.insert_transaction(conn, normalised)
                        if inserted:
                            inserted_rows_count += 1

                # Record file hash to ensure file-level idempotency on next runs
                self.db_manager.record_processed_file(conn, file_hash, file_name)
            
            # Commit connection
            conn.commit()

        end_time = time.time()
        end_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        duration = end_time - start_time

        # Generate summary report
        summary = write_summary(
            summary_dir=self.summary_dir,
            run_id=run_id,
            start_time=start_timestamp,
            end_time=end_timestamp,
            duration=duration,
            files_processed=processed_files_list,
            total_rows=total_rows_read,
            valid_rows=valid_rows_processed,
            quarantined_rows=quarantined_rows_count,
            inserted_rows=inserted_rows_count,
            status="SUCCESS"
        )

        logger.info(f"Pipeline run {run_id} completed. Status: SUCCESS, Loaded: {inserted_rows_count}, Quarantined: {quarantined_rows_count}")
        return summary
