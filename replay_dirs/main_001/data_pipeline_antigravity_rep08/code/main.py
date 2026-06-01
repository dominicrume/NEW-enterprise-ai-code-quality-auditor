#!/usr/bin/env python3
"""
CLI Entrypoint for the data pipeline.
Integrates command line arguments with config.yaml, sets up logging,
and runs the pipeline in either single-run or scheduled mode.
"""

import os
import sys
import argparse
import logging
import yaml
from pathlib import Path

from pipeline import DataPipeline
from pipeline.schedule import start_scheduler

def setup_logging() -> logging.Logger:
    """
    Sets up the logging configuration.
    Governance: Employs safe logging where no raw CSV values (PII) are printed.
    """
    logger = logging.getLogger("data_pipeline")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

def load_yaml_config(config_path: str = "config.yaml") -> dict:
    """
    Loads configurations from config.yaml if it exists.
    """
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    config = loaded
        except Exception as e:
            # Safe generic log
            print(f"Warning: Failed to load config file: {str(e)}", file=sys.stderr)
    return config

def main():
    logger = setup_logging()
    logger.info("Initializing Data Pipeline CLI Application")
    
    # 1. Load YAML Configuration
    yaml_config = load_yaml_config()
    pipeline_cfg = yaml_config.get("pipeline", {})
    schedule_cfg = yaml_config.get("schedule", {})
    
    # 2. Setup argument parser
    parser = argparse.ArgumentParser(
        description="ETL Data Pipeline CLI with scheduling, schema validation, and SQLite loading."
    )
    
    # Directory overrides
    parser.add_argument(
        "--input-dir",
        default=pipeline_cfg.get("input_dir", "input"),
        help="Directory containing input CSV files."
    )
    parser.add_argument(
        "--db-path",
        default=pipeline_cfg.get("db_path", "pipeline.db"),
        help="SQLite database file path."
    )
    parser.add_argument(
        "--quarantine-dir",
        default=pipeline_cfg.get("quarantine_dir", "quarantine"),
        help="Directory to store quarantine CSV files."
    )
    parser.add_argument(
        "--summary-dir",
        default=pipeline_cfg.get("summary_dir", "summaries"),
        help="Directory to store run summary JSON files."
    )
    
    # Scheduling options
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run the application in scheduled mode (infinite loop)."
    )
    parser.add_argument(
        "--cron",
        default=schedule_cfg.get("cron"),
        help="Cron expression for daily scheduling (e.g. '0 0 * * *'). Overrides --time."
    )
    parser.add_argument(
        "--time",
        default=schedule_cfg.get("time", "00:00"),
        help="Daily run time in HH:MM format (default: '00:00')."
    )
    
    args = parser.parse_args()
    
    # Resolve relative paths relative to current working directory
    input_dir = os.path.abspath(args.input_dir)
    db_path = os.path.abspath(args.db_path)
    quarantine_dir = os.path.abspath(args.quarantine_dir)
    summary_dir = os.path.abspath(args.summary_dir)
    
    # 3. Create pipeline instance
    pipeline = DataPipeline(
        input_dir=input_dir,
        db_path=db_path,
        quarantine_dir=quarantine_dir,
        summary_dir=summary_dir
    )
    
    if args.schedule:
        # Define execution closure
        def scheduled_job():
            logger.info("Executing scheduled pipeline run...")
            try:
                summary = pipeline.run()
                logger.info(
                    f"Scheduled run completed. Status: {summary['status']}, "
                    f"Processed: {summary['valid_rows_processed']}, "
                    f"Quarantined: {summary['quarantined_rows_count']}"
                )
            except Exception as e:
                logger.error(f"Scheduled pipeline run encountered an error: {str(e)}")
        
        logger.info("Starting scheduler. Press Ctrl+C to terminate.")
        try:
            start_scheduler(scheduled_job, cron_string=args.cron, schedule_time=args.time)
        except (KeyboardInterrupt, SystemExit):
            logger.info("CLI scheduler shutdown requested. Exiting.")
    else:
        # Single run execution
        try:
            summary = pipeline.run()
            logger.info("Single run pipeline execution completed successfully.")
            print("\n================ Run Summary ================")
            print(f"Run ID:                 {summary['run_id']}")
            print(f"Status:                 {summary['status']}")
            print(f"Start Time:             {summary['start_time']}")
            print(f"End Time:               {summary['end_time']}")
            print(f"Duration (seconds):     {summary['duration_seconds']}")
            print(f"Files Processed:        {', '.join(summary['files_processed'])}")
            print(f"Total Rows Read:        {summary['total_rows_read']}")
            print(f"Valid Rows Processed:   {summary['valid_rows_processed']}")
            print(f"Quarantined Rows:       {summary['quarantined_rows_count']}")
            print(f"SQLite Loaded Rows:     {summary['inserted_rows_count']}")
            print("=============================================\n")
            
            if summary["status"] == "FAILED":
                sys.exit(1)
        except Exception as e:
            logger.error(f"Data pipeline execution failed: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main()
