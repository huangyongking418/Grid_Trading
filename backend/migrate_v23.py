# -*- coding: utf-8 -*-
"""
v2.3 database migration:
- email_config keeps only per-user recipient fields (to_email, enabled)
- move SMTP sender configuration into system_param

Usage: run `python migrate_v23.py` from the backend directory.
"""

from sqlalchemy import create_engine, inspect, text

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)

CREATE_EMAIL_CONFIG = """
CREATE TABLE IF NOT EXISTS email_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL DEFAULT 1,
    to_email VARCHAR(255) NOT NULL DEFAULT '',
    enabled TINYINT(1) NOT NULL DEFAULT 0,
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_email_config_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def upsert_param(conn, key: str, value: str) -> None:
    conn.execute(
        text(
            "INSERT INTO system_param (param_key, param_value, description, create_time, update_time) "
            "VALUES (:k, :v, 'email smtp setting', NOW(), NOW()) "
            "ON DUPLICATE KEY UPDATE param_value = VALUES(param_value), update_time = NOW()"
        ),
        {"k": key, "v": value},
    )


def main() -> None:
    print("=== v2.3 migration start ===")
    insp = inspect(engine)
    if "email_config" not in insp.get_table_names():
        with engine.begin() as conn:
            conn.execute(text(CREATE_EMAIL_CONFIG))
        print("  + email_config table created (new structure)")
    else:
        cols = {c["name"] for c in insp.get_columns("email_config")}
        if "smtp_host" in cols:
            with engine.begin() as conn:
                rows = conn.execute(
                    text(
                        "SELECT smtp_host, smtp_port, smtp_user, smtp_password, "
                        "from_email, enabled FROM email_config "
                        "WHERE smtp_host <> '' ORDER BY id LIMIT 1"
                    )
                ).fetchall()
                if rows:
                    row = rows[0]
                    upsert_param(conn, "email_smtp_host", str(row[0] or ""))
                    upsert_param(conn, "email_smtp_port", str(row[1] or 465))
                    upsert_param(conn, "email_smtp_user", str(row[2] or ""))
                    upsert_param(conn, "email_smtp_password", str(row[3] or ""))
                    upsert_param(conn, "email_from_email", str(row[4] or ""))
                    upsert_param(conn, "email_enabled", "1" if row[5] else "0")
                conn.execute(
                    text(
                        "ALTER TABLE email_config "
                        "DROP COLUMN smtp_host, "
                        "DROP COLUMN smtp_port, "
                        "DROP COLUMN smtp_user, "
                        "DROP COLUMN smtp_password, "
                        "DROP COLUMN from_email"
                    )
                )
            print("  + email_config migrated to recipient-only fields")
        else:
            print("  = email_config already has new structure")
    print("=== v2.3 migration done ===")


if __name__ == "__main__":
    main()
