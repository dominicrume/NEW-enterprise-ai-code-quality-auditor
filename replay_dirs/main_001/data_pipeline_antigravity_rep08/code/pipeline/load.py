"""
Loading module for the data pipeline.
Manages connections and idempotent operations in the SQLite database.
"""

import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Dict, Any, Generator

logger = logging.getLogger("data_pipeline.load")

class DatabaseManager:
    """
    Manages SQLite database connections, schema setup, and transactions.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for SQLite database connection.
        Automatically commits changes and closes the connection on exit.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def initialize_schema(self):
        """
        Creates the database tables if they do not exist.
        """
        logger.info(f"Initializing database schema at: {self.db_path}")
        with self.connect() as conn:
            cursor = conn.cursor()
            
            # transactions table. transaction_id as PRIMARY KEY enforces row-level idempotency
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
            
            # processed_files table. file_hash as PRIMARY KEY enforces file-level idempotency
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_files (
                    file_hash TEXT PRIMARY KEY,
                    file_name TEXT,
                    processed_at TEXT
                )
            """)
            conn.commit()

    def is_file_processed(self, conn: sqlite3.Connection, file_hash: str) -> bool:
        """
        Checks if a file with the given hash has already been processed.
        """
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM processed_files WHERE file_hash = ?", (file_hash,))
        return cursor.fetchone() is not None

    def record_processed_file(self, conn: sqlite3.Connection, file_hash: str, file_name: str):
        """
        Records that a file has been successfully processed.
        """
        cursor = conn.cursor()
        processed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        cursor.execute("""
            INSERT OR IGNORE INTO processed_files (file_hash, file_name, processed_at)
            VALUES (?, ?, ?)
        """, (file_hash, file_name, processed_at))

    def insert_transaction(self, conn: sqlite3.Connection, row: Dict[str, Any]) -> bool:
        """
        Idempotently inserts a transaction row into SQLite database.
        Returns:
            True if a new row was inserted, False if ignored (duplicate transaction_id).
        """
        cursor = conn.cursor()
        processed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        cursor.execute("""
            INSERT OR IGNORE INTO transactions (
                transaction_id, product_id, price, quantity, category, processed_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            row["transaction_id"],
            row["product_id"],
            row["price"],
            row["quantity"],
            row["category"],
            processed_at
        ))
        
        return cursor.rowcount > 0
