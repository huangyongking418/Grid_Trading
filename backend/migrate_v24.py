# -*- coding: utf-8 -*-
"""
v2.4 database migration:
- add backtest_manage / document_view permissions for preset roles
- 管理员: backtest_manage all, document_view all
- 普通用户: backtest_manage self, document_view self

Usage: run `python migrate_v24.py` from the backend directory.
"""

from sqlalchemy import create_engine, text

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)

PRESET_PERMISSIONS = {
    "管理员": [
        ("backtest_manage", "all"),
        ("document_view", "all"),
    ],
    "普通用户": [
        ("backtest_manage", "self"),
        ("document_view", "self"),
    ],
}


def main() -> None:
    print("=== v2.4 migration start ===")
    with engine.begin() as conn:
        for role_name, perms in PRESET_PERMISSIONS.items():
            role_ids = conn.execute(
                text("SELECT id FROM role WHERE name = :n AND is_preset = 1"),
                {"n": role_name},
            ).fetchall()
            if not role_ids:
                print(f"  = preset role '{role_name}' not found, skip")
                continue
            for role_id in role_ids:
                for code, scope in perms:
                    exists = conn.execute(
                        text(
                            "SELECT 1 FROM role_permission "
                            "WHERE role_id = :rid AND function_code = :c"
                        ),
                        {"rid": role_id[0], "c": code},
                    ).first()
                    if exists:
                        print(f"  = role {role_id[0]} ({role_name}) already has {code}, skip")
                        continue
                    conn.execute(
                        text(
                            "INSERT INTO role_permission (role_id, function_code, data_scope, create_time) "
                            "VALUES (:rid, :c, :s, NOW())"
                        ),
                        {"rid": role_id[0], "c": code, "s": scope},
                    )
                    print(f"  + role {role_id[0]} ({role_name}) + {code} ({scope})")
    print("=== v2.4 migration done ===")


if __name__ == "__main__":
    main()
