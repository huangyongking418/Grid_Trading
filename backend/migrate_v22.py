# -*- coding: utf-8 -*-
"""
v2.2 database migration:
- create email_config table
- add operation_log.push_status JSON column

Usage: run `python migrate_v22.py` from the backend directory.
"""

from sqlalchemy import create_engine, inspect, text

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)

CREATE_EMAIL_CONFIG = """
CREATE TABLE IF NOT EXISTS email_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL DEFAULT 1,
    smtp_host VARCHAR(128) NOT NULL DEFAULT '',
    smtp_port INT NOT NULL DEFAULT 465,
    smtp_user VARCHAR(128) NOT NULL DEFAULT '',
    smtp_password VARCHAR(255) NOT NULL DEFAULT '',
    from_email VARCHAR(128) NOT NULL DEFAULT '',
    to_email VARCHAR(255) NOT NULL DEFAULT '',
    enabled TINYINT(1) NOT NULL DEFAULT 0,
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_email_config_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def add_column_if_missing(table: str, column_def: str) -> None:
    col_name = column_def.split()[0]
    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns(table)}
    if col_name in cols:
        print(f"  = {table}.{col_name} already exists, skip")
        return
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE `{table}` ADD COLUMN {column_def}"))
    print(f"  + {table}.{col_name} added")


def main() -> None:
    print("=== v2.2 migration start ===")
    with engine.begin() as conn:
        conn.execute(text(CREATE_EMAIL_CONFIG))
    print("  + email_config table ensured")
    add_column_if_missing("operation_log", "push_status JSON NULL")
    print("=== v2.2 migration done ===")


if __name__ == "__main__":
    main()
