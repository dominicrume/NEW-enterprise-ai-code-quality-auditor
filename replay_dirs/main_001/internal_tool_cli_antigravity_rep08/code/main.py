#!/usr/bin/env python3
"""
CLI entrypoint for the data pipeline.
"""
import os
import sys
import argparse
import logging
from pipeline import DataPipeline
from scheduler import start_scheduler

def setup_logging():
    """Sets up a secure logger that does not output or log sensitive row information (PII)."""
    logger = logging.getLogger("data_pipeline")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        # Professional, clear formatting
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def main():
    parser = argparse.ArgumentParser(
        description="ETL Data Pipeline CLI with scheduling, schema validation, and SQLite load."
    )
    
    # Configure directories and files
    parser.add_argument(
        "--input-dir",
        default="input",
        help="Local input directory for reading CSV files (default: 'input')"
    )
    parser.add_argument(
        "--db-path",
        default="pipeline.db",
        help="Local SQLite database file path (default: 'pipeline.db')"
    )
    parser.add_argument(
        "--quarantine-dir",
        default="quarantine",
        help="Directory to write invalid/quarantined rows (default: 'quarantine')"
    )
    parser.add_argument(
        "--summary-dir",
        default="summaries",
        help="Directory to write JSON run summaries (default: 'summaries')"
    )
    
    # Scheduling arguments
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run the pipeline in scheduler mode"
    )
    parser.add_argument(
        "--cron",
        help="Cron expression for scheduling (e.g. '0 0 * * *' for daily at midnight)"
    )
    parser.add_argument(
        "--time",
        default="00:00",
        help="Daily execution time in HH:MM format (default: '00:00')"
    )
    
    args = parser.parse_args()
    
    logger = setup_logging()
    logger.info("Starting data_pipeline CLI application")
    
    # Initialise the pipeline
    pipeline = DataPipeline(
        input_dir=args.input_dir,
        db_path=args.db_path,
        quarantine_dir=args.quarantine_dir,
        summary_dir=args.summary_dir
    )
    
    if args.schedule:
        # Define the job execution closure
        def job():
            logger.info("Executing scheduled pipeline run...")
            try:
                summary = pipeline.run()
                logger.info(f"Pipeline finished. Status: {summary['status']}, Inserted: {summary['inserted_rows_count']}, Quarantined: {summary['quarantined_rows_count']}")
            except Exception as e:
                logger.error(f"Scheduled job encountered an error: {str(e)}")
        
        try:
            start_scheduler(job, cron_string=args.cron, schedule_time=args.time)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler shutdown complete.")
    else:
        # Single execution run
        try:
            summary = pipeline.run()
            logger.info("Pipeline execution complete.")
            print(f"Run ID: {summary['run_id']}")
            print(f"Status: {summary['status']}")
            print(f"Total Rows Read: {summary['total_rows_read']}")
            print(f"Valid Rows: {summary['valid_rows_processed']}")
            print(f"Quarantined Rows: {summary['quarantined_rows_count']}")
            print(f"Loaded Rows: {summary['inserted_rows_count']}")
            print(f"Duration: {summary['duration_seconds']}s")
            
            if summary["status"] == "FAILED":
                sys.exit(1)
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main()
