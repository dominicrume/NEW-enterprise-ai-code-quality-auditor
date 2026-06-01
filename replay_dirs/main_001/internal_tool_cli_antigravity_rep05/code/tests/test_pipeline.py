"""
Unit tests for the ETL pipeline.
"""
import os
import csv
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime

from schema import validate_row
from pipeline import DataPipeline
from scheduler import run_standard_loop

class TestDataPipeline(unittest.TestCase):
    def setUp(self):
        # Create temporary directories for testing
        self.test_dir = tempfile.TemporaryDirectory()
        self.input_dir = os.path.join(self.test_dir.name, "input")
        self.quarantine_dir = os.path.join(self.test_dir.name, "quarantine")
        self.summary_dir = os.path.join(self.test_dir.name, "summaries")
        self.db_path = os.path.join(self.test_dir.name, "pipeline.db")
        
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.quarantine_dir, exist_ok=True)
        os.makedirs(self.summary_dir, exist_ok=True)

    def tearDown(self):
        # Clean up temporary directories
        self.test_dir.cleanup()

    def test_schema_validation(self):
        # Test valid row
        valid_row = {
            "transaction_id": "TXN_001",
            "product_id": "PROD_ABC",
            "price": "99.954",
            "quantity": "5",
            "category": "Electronics"
        }
        is_valid, validated, error = validate_row(valid_row)
        self.assertTrue(is_valid)
        self.assertEqual(validated["transaction_id"], "TXN_001")
        self.assertEqual(validated["price"], 99.954)
        self.assertEqual(validated["quantity"], 5)
        self.assertEqual(validated["category"], "Electronics")
        self.assertIsNone(error)
        
        # Test missing required field
        invalid_row_1 = {
            "transaction_id": "",
            "product_id": "PROD_ABC",
            "price": "99.954",
            "quantity": "5"
        }
        is_valid, validated, error = validate_row(invalid_row_1)
        self.assertFalse(is_valid)
        self.assertIn("Missing required field", error)
        self.assertIsNone(validated)
        
        # Test invalid float type
        invalid_row_2 = {
            "transaction_id": "TXN_002",
            "product_id": "PROD_ABC",
            "price": "not-a-float",
            "quantity": "5"
        }
        is_valid, validated, error = validate_row(invalid_row_2)
        self.assertFalse(is_valid)
        self.assertIn("Invalid type for field 'price'", error)
        
        # Test invalid integer type
        invalid_row_3 = {
            "transaction_id": "TXN_003",
            "product_id": "PROD_ABC",
            "price": "10.50",
            "quantity": "2.5" # floats are not valid integers
        }
        is_valid, validated, error = validate_row(invalid_row_3)
        self.assertFalse(is_valid)
        self.assertIn("Invalid type for field 'quantity'", error)

    def test_pipeline_normalisation_and_sqlite_load(self):
        # Create a sample valid CSV file
        csv_data = [
            ["transaction_id", "product_id", "price", "quantity", "category"],
            ["TXN_001", "PROD_UPPERCASE", "19.999", "3", "CLOTHING"],
            ["TXN_002", "PROD_XYZ", "10.004", "1", ""]
        ]
        
        csv_path = os.path.join(self.input_dir, "test_data.csv")
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
            
        pipeline = DataPipeline(
            input_dir=self.input_dir,
            db_path=self.db_path,
            quarantine_dir=self.quarantine_dir,
            summary_dir=self.summary_dir
        )
        
        summary = pipeline.run()
        
        # Verify counts in summary
        self.assertEqual(summary["total_rows_read"], 2)
        self.assertEqual(summary["valid_rows_processed"], 2)
        self.assertEqual(summary["quarantined_rows_count"], 0)
        self.assertEqual(summary["inserted_rows_count"], 2)
        self.assertEqual(summary["status"], "SUCCESS")
        
        # Verify SQLite data (normalisation: lowercasing and rounding)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT transaction_id, product_id, price, quantity, category FROM transactions ORDER BY transaction_id")
        rows = cursor.fetchall()
        conn.close()
        
        self.assertEqual(len(rows), 2)
        # TXN_001 product_id "PROD_UPPERCASE" -> "prod_uppercase"
        # price 19.999 rounded -> 20.0
        # category "CLOTHING" -> "clothing"
        self.assertEqual(rows[0], ("TXN_001", "prod_uppercase", 20.0, 3, "clothing"))
        # TXN_002 price 10.004 rounded -> 10.00
        # category empty -> None
        self.assertEqual(rows[1], ("TXN_002", "prod_xyz", 10.0, 1, None))

    def test_idempotent_loads(self):
        # Create a sample CSV file
        csv_data = [
            ["transaction_id", "product_id", "price", "quantity", "category"],
            ["TXN_DUPE", "PROD_001", "15.50", "2", "Books"]
        ]
        
        csv_path = os.path.join(self.input_dir, "test_dupe.csv")
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
            
        pipeline = DataPipeline(
            input_dir=self.input_dir,
            db_path=self.db_path,
            quarantine_dir=self.quarantine_dir,
            summary_dir=self.summary_dir
        )
        
        # Run 1
        summary1 = pipeline.run()
        self.assertEqual(summary1["inserted_rows_count"], 1)
        
        # Run 2 on same input
        summary2 = pipeline.run()
        # Should process 1 row but insert 0 because of idempotent unique constraint
        self.assertEqual(summary2["total_rows_read"], 1)
        self.assertEqual(summary2["valid_rows_processed"], 1)
        self.assertEqual(summary2["inserted_rows_count"], 0)
        
        # Verify only 1 record exists in DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM transactions WHERE transaction_id = 'TXN_DUPE'")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(count, 1)

    def test_validation_quarantine(self):
        # Create CSV with 1 valid row and 1 invalid row
        csv_data = [
            ["transaction_id", "product_id", "price", "quantity", "category"],
            ["TXN_VALID", "PROD_A", "10.00", "1", "Food"],
            ["TXN_INVALID", "PROD_B", "invalid-price", "2", "Food"]
        ]
        
        csv_path = os.path.join(self.input_dir, "test_mixed.csv")
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
            
        pipeline = DataPipeline(
            input_dir=self.input_dir,
            db_path=self.db_path,
            quarantine_dir=self.quarantine_dir,
            summary_dir=self.summary_dir
        )
        
        summary = pipeline.run()
        self.assertEqual(summary["total_rows_read"], 2)
        self.assertEqual(summary["valid_rows_processed"], 1)
        self.assertEqual(summary["quarantined_rows_count"], 1)
        self.assertEqual(summary["inserted_rows_count"], 1)
        
        # Check that quarantine file was generated and contains the invalid row
        quarantine_files = os.listdir(self.quarantine_dir)
        self.assertEqual(len(quarantine_files), 1)
        
        quarantine_path = os.path.join(self.quarantine_dir, quarantine_files[0])
        with open(quarantine_path, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["transaction_id"], "TXN_INVALID")
        self.assertEqual(rows[0]["price"], "invalid-price")
        self.assertEqual(rows[0]["quarantine_reason"], "Invalid type for field 'price' (expected float)")

    def test_run_summary_json(self):
        pipeline = DataPipeline(
            input_dir=self.input_dir,
            db_path=self.db_path,
            quarantine_dir=self.quarantine_dir,
            summary_dir=self.summary_dir
        )
        
        summary = pipeline.run()
        run_id = summary["run_id"]
        
        summary_file = os.path.join(self.summary_dir, f"summary_{run_id}.json")
        self.assertTrue(os.path.exists(summary_file))
        
        with open(summary_file, mode="r", encoding="utf-8") as f:
            loaded_summary = json.load(f)
            
        self.assertEqual(loaded_summary["run_id"], run_id)
        self.assertEqual(loaded_summary["status"], "SUCCESS")
        self.assertIn("duration_seconds", loaded_summary)
        self.assertIn("start_time", loaded_summary)
        self.assertIn("end_time", loaded_summary)
        
if __name__ == "__main__":
    unittest.main()
