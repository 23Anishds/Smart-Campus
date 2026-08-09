import sqlite3
import traceback
from typing import Optional, Any
from config import AppConfig

config = AppConfig.get_config()

class DatabaseConnection:
    """
    Context manager for handling SQLite database connections safely.
    Handles commit on success and rollback on exceptions.
    Demonstrates Context Managers (Concept #4).
    """
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

    def __enter__(self) -> sqlite3.Cursor:
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
            self.cursor = self.conn.cursor()
            return self.cursor
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            raise

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]) -> bool:
        if self.conn and self.cursor:
            if exc_type is None:
                # No exception, commit transaction
                try:
                    self.conn.commit()
                except sqlite3.Error as e:
                    print(f"Commit error: {e}")
            else:
                # Exception occurred, rollback transaction
                print(f"Rolling back due to: {exc_val}")
                try:
                    self.conn.rollback()
                except sqlite3.Error as e:
                    print(f"Rollback error: {e}")
            
            self.cursor.close()
            self.conn.close()
        
        # Return False to propagate exceptions, True to suppress
        return False
