"""
Reporting module for the data pipeline.
Generates and writes structured JSON summaries of each ETL execution run.
"""

import os
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger("data_pipeline.report")

def write_summary(
    summary_dir: str,
    run_id: str,
    start_time: str,
    end_time: str,
    duration: float,
    files_processed: List[str],
    total_rows: int,
    valid_rows: int,
    quarantined_rows: int,
    inserted_rows: int,
    status: str
) -> Dict[str, Any]:
    """
    Constructs a run execution summary dict, writes it to a JSON file, and returns it.
    """
    summary = {
        "run_id": run_id,
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": round(duration, 4),
        "files_processed": files_processed,
        "total_rows_read": total_rows,
        "valid_rows_processed": valid_rows,
        "quarantined_rows_count": quarantined_rows,
        "inserted_rows_count": inserted_rows,
        "status": status
    }
    
    os.makedirs(summary_dir, exist_ok=True)
    summary_file_path = os.path.join(summary_dir, f"summary_{run_id}.json")
    
    try:
        with open(summary_file_path, mode="w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Execution run summary written to: {summary_file_path}")
    except Exception as e:
        logger.error(f"Failed to write summary file: {str(e)}")
        
    return summary
