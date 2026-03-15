"""
Database Module - SQLite for user and family data
"""

import sqlite3
from typing import List, Optional, Dict, Tuple
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


class Database:
    """Handle all database operations"""
    
    def __init__(self, db_path: str = "scam_detector.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    chat_id INTEGER UNIQUE NOT NULL,
                    name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    enabled INTEGER DEFAULT 1
                )
            """)
            
            # Family members table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS family_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    family_chat_id INTEGER NOT NULL,
                    relationship TEXT,
                    name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Detection logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detection_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    message_text TEXT,
                    rule_score INTEGER,
                    ai_score INTEGER,
                    final_score INTEGER,
                    risk_level TEXT,
                    alerted_family BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def add_user(self, chat_id: int, name: str = None) -> bool:
        """Add new user to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (chat_id, name)
                VALUES (?, ?)
            """, (chat_id, name))
            
            conn.commit()
            conn.close()
            logger.info(f"User {chat_id} added successfully")
            return True
            
        except sqlite3.IntegrityError:
            logger.info(f"User {chat_id} already exists")
            return False
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def get_user(self, chat_id: int) -> Optional[Dict]:
        """Get user information"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, chat_id, name FROM users WHERE chat_id = ?
            """, (chat_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def add_family_member(self, user_id: int, family_chat_id: int, 
                         name: str = None, relationship: str = None) -> bool:
        """Add family member for notifications"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO family_members (user_id, family_chat_id, name, relationship)
                VALUES (?, ?, ?, ?)
            """, (user_id, family_chat_id, name, relationship))
            
            conn.commit()
            conn.close()
            logger.info(f"Family member added for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding family member: {e}")
            return False
    
    def get_family_members(self, user_id: int) -> List[Dict]:
        """Get all family members for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT family_chat_id, name, relationship FROM family_members 
                WHERE user_id = ?
            """, (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting family members: {e}")
            return []
    
    def log_detection(self, user_id: int, message: str, 
                     rule_score: int, ai_score: int, final_score: int,
                     risk_level: str, alerted_family: bool = False) -> bool:
        """Log a scam detection event"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO detection_logs 
                (user_id, message_text, rule_score, ai_score, final_score, risk_level, alerted_family)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, message[:500], rule_score, ai_score, final_score, risk_level, alerted_family))
            
            conn.commit()
            conn.close()
            logger.info(f"Detection logged for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging detection: {e}")
            return False
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get statistics for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_detections,
                    SUM(CASE WHEN risk_level = 'ALERT' THEN 1 ELSE 0 END) as alerts,
                    SUM(CASE WHEN risk_level = 'WARNING' THEN 1 ELSE 0 END) as warnings,
                    SUM(CASE WHEN alerted_family THEN 1 ELSE 0 END) as family_alerts,
                    AVG(final_score) as avg_score
                FROM detection_logs
                WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "total_detections": row[0] or 0,
                    "alerts": row[1] or 0,
                    "warnings": row[2] or 0,
                    "family_alerts": row[3] or 0,
                    "avg_score": round(row[4], 1) if row[4] else 0
                }
            
            return {
                "total_detections": 0,
                "alerts": 0,
                "warnings": 0,
                "family_alerts": 0,
                "avg_score": 0
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}
    
    def is_user_active(self, chat_id: int) -> bool:
        """Check if a user/family member has started the bot (is active)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT user_id FROM users WHERE chat_id = ?", (chat_id,))
            result = cursor.fetchone()
            conn.close()
            
            is_active = result is not None
            if not is_active:
                logger.info(f"User {chat_id} is NOT active - hasn't started bot yet")
            return is_active
            
        except Exception as e:
            logger.error(f"Error checking user active status: {e}")
            return False


# Global database instance
db = Database("scam_detector.db")
