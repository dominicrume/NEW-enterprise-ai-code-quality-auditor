# Data Pipeline CLI

A robust Python command-line tool that reads CSV files from a configurable directory, validates and normalises the data, loads it into a SQLite database, schedules daily execution, and exports execution summaries.

## Features

- **CSV Ingestion (`ingest.csv`)**: Reads CSV files from a configurable directory.
- **Schema Validation (`validate.schema`)**: Validates rows against a pre-declared column schema. Defective or invalid rows are rejected and written to a quarantined CSV file. No PII is logged in stdout or standard log files.
- **Transformation (`transform.normalise`)**: Automatically normalises text columns to lowercase and rounds numeric values to two decimal places.
- **SQLite Loading (`load.sqlite`)**: Inserts valid, normalised records into a local SQLite table (`transactions`).
- **Scheduler (`schedule.daily`)**: Schedules daily execution via `APScheduler` or a built-in time-sleep loop fallback.
- **Run Summary JSON Reporting (`report.run_summary`)**: Generates structured execution logs with row counts, duration, and status.

## Governance Rules

1. **No PII**: The default schema does not collect or log personally identifiable information. Any error logging redacts specific column content, logging only field names and type mismatches.
2. **Idempotent Loads**: The SQLite target uses the `transaction_id` column as a Primary Key. Re-running the pipeline on duplicate files uses `INSERT OR IGNORE` which guarantees that duplicate rows are not created.
3. **No External Calls**: The pipeline runs entirely locally. It does not perform network socket connections or contact any external API.

## Installation

Ensure you have Python 3 installed. You can optionally install project dependencies:

```bash
pip install -r requirements.txt
```

*Note: If `apscheduler` is not installed, the daily scheduler automatically falls back to standard-library intervals.*

## Usage

### Run ETL Once
Place your `.csv` files into the `input` directory (configurable) and run:

```bash
python main.py
```

### Options

- `--input-dir <path>`: Local input directory for reading CSV files (default: `input`)
- `--db-path <path>`: Local SQLite database file path (default: `pipeline.db`)
- `--quarantine-dir <path>`: Directory to write invalid/quarantined rows (default: `quarantine`)
- `--summary-dir <path>`: Directory to write JSON run summaries (default: `summaries`)
- `--schedule`: Run the pipeline in scheduler mode
- `--cron <cron_expr>`: Cron expression for scheduling (e.g. `0 0 * * *` for daily at midnight)
- `--time <HH:MM>`: Daily execution time (default: `00:00`)

### Run in Scheduler Mode
To run the scheduler daily at midnight:
```bash
python main.py --schedule --time 00:00
```

## Schema Format

The system validates against a transaction schema:
- `transaction_id` (string, required)
- `product_id` (string, required)
- `price` (float, required)
- `quantity` (int, required)
- `category` (string, optional)
