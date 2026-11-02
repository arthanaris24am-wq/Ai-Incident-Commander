from .extensions import db
from sqlalchemy import text


def init_db(app):

    with app.app_context():
        db.create_all()
        
        # SQLite simplistic migration: add missing columns to Incident
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(incidents);"))
                columns = [row[1] for row in result]
                
                if "root_cause" not in columns:
                    conn.execute(text("ALTER TABLE incidents ADD COLUMN root_cause TEXT"))
                if "confidence" not in columns:
                    conn.execute(text("ALTER TABLE incidents ADD COLUMN confidence FLOAT"))
                if "recommendation" not in columns:
                    conn.execute(text("ALTER TABLE incidents ADD COLUMN recommendation TEXT"))
                if "fingerprint" not in columns:
                    conn.execute(text("ALTER TABLE incidents ADD COLUMN fingerprint TEXT"))
                if "remediation_attempts" not in columns:
                    conn.execute(text("ALTER TABLE incidents ADD COLUMN remediation_attempts INTEGER DEFAULT 0"))
                
                result_actions = conn.execute(text("PRAGMA table_info(incident_actions);"))
                actions_columns = [row[1] for row in result_actions]
                
                actions_schema = {
                    "target": "TEXT",
                    "risk_level": "TEXT DEFAULT 'SAFE'",
                    "confidence": "FLOAT",
                    "automation_allowed": "BOOLEAN DEFAULT 0",
                    "executed_at": "DATETIME",
                    "executed_by": "TEXT",
                    "result": "TEXT",
                    "error": "TEXT",
                    "duration": "FLOAT"
                }
                
                for col, col_type in actions_schema.items():
                    if col not in actions_columns:
                        conn.execute(text(f"ALTER TABLE incident_actions ADD COLUMN {col} {col_type}"))
                    
                conn.commit()
        except Exception as e:
            print(f"Error checking/migrating schema: {e}")