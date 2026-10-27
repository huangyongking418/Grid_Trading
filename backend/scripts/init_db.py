"""Create the schema and seed the minimum data required by the application.

Run from the backend directory:
    python scripts/init_db.py --admin-username admin --admin-phone 13800000000

The script is idempotent and does not overwrite existing roles, permissions,
templates, parameters, or users.
"""

from __future__ import annotations

import argparse
import getpass
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.auth import hash_password
from app.core.database import Base, SessionLocal, engine
from app.models.all_models import (
    Role,
    RolePermission,
    StrategyTemplate,
    SystemParam,
    User,
)


ROLE_PERMISSIONS = {
    "管理员": {
        "description": "全部功能和全部数据权限",
        "permissions": {
            "strategy_manage": "all",
            "stock_manage": "all",
            "operation_detail": "all",
            "monitor_config": "all",
            "profit_analysis": "all",
            "message_center": "all",
            "system_manage": "all",
            "backtest_manage": "all",
            "document_view": "all",
        },
    },
    "普通用户": {
        "description": "个人数据权限",
        "permissions": {
            "strategy_manage": "self",
            "stock_manage": "self",
            "operation_detail": "self",
            "monitor_config": "self",
            "profit_analysis": "self",
            "message_center": "self",
            "backtest_manage": "self",
            "document_view": "self",
        },
    },
}

STRATEGY_TEMPLATES = [
    {
        "name": "震荡向上策略",
        "description": "价格中枢缓慢上移，卖出间距大于买入间距",
        "direction_type": "oscillation_up",
        "default_params": {
            "grid_layers": 8,
            "grid_spacing": 2.0,
            "asymmetry_ratio": 1.6,
            "fund_allocation": "equal",
            "stop_loss_strategy": "none",
        },
    },
    {
        "name": "震荡策略",
        "description": "价格在区间内反复波动，买卖间距对称",
        "direction_type": "oscillation",
        "default_params": {
            "grid_layers": 6,
            "grid_spacing": 2.0,
            "asymmetry_ratio": 1.0,
            "fund_allocation": "equal",
            "stop_loss_strategy": "none",
        },
    },
    {
        "name": "震荡向下策略",
        "description": "价格中枢缓慢下移，买入间距大于卖出间距",
        "direction_type": "oscillation_down",
        "default_params": {
            "grid_layers": 5,
            "grid_spacing": 3.0,
            "asymmetry_ratio": 0.67,
            "fund_allocation": "equal",
            "stop_loss_strategy": "stop_layer",
        },
    },
]

DEFAULT_PARAMS = {
    "account_expire_days": ("5", "新注册用户账号默认有效天数"),
    "scheduler_enabled": ("1", "监控定时任务总开关"),
    "scheduler_interval_minutes": ("15", "监控定时任务轮询间隔（分钟）"),
}


def seed_roles(db) -> None:
    for role_name, config in ROLE_PERMISSIONS.items():
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(
                name=role_name,
                description=config["description"],
                is_preset=True,
            )
            db.add(role)
            db.flush()
            print(f"  + role: {role_name}")

        existing = {
            item.function_code
            for item in db.query(RolePermission)
            .filter(RolePermission.role_id == role.id)
            .all()
        }
        for function_code, data_scope in config["permissions"].items():
            if function_code in existing:
                continue
            db.add(
                RolePermission(
                    role_id=role.id,
                    function_code=function_code,
                    data_scope=data_scope,
                )
            )
            print(f"  + permission: {role_name} / {function_code} ({data_scope})")


def seed_templates(db) -> None:
    existing = {
        item[0]
        for item in db.query(StrategyTemplate.direction_type).all()
    }
    for template in STRATEGY_TEMPLATES:
        if template["direction_type"] in existing:
            continue
        db.add(StrategyTemplate(**template))
        print(f"  + strategy template: {template['name']}")


def seed_params(db) -> None:
    for key, (value, description) in DEFAULT_PARAMS.items():
        if db.query(SystemParam).filter(SystemParam.param_key == key).first():
            continue
        db.add(
            SystemParam(
                param_key=key,
                param_value=value,
                description=description,
            )
        )
        print(f"  + system parameter: {key}={value}")


def create_admin(
    db,
    username: str,
    phone: str,
    password: str,
    expire_days: int,
) -> None:
    if db.query(User).filter(User.username == username).first():
        print(f"  = admin user already exists: {username}")
        return
    if db.query(User).filter(User.phone == phone).first():
        raise SystemExit(f"手机号已被其他账号使用：{phone}")

    admin_role = db.query(Role).filter(Role.name == "管理员").first()
    if not admin_role:
        raise SystemExit("管理员角色初始化失败")

    db.add(
        User(
            username=username,
            password_hash=hash_password(password),
            phone=phone,
            role_id=admin_role.id,
            status="active",
            expire_date=datetime.now() + timedelta(days=expire_days),
        )
    )
    print(f"  + admin user: {username}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="初始化网格交易系统数据库")
    parser.add_argument("--admin-username", help="管理员登录账号")
    parser.add_argument("--admin-phone", help="管理员手机号")
    parser.add_argument(
        "--admin-expire-days",
        type=int,
        default=3650,
        help="管理员账号有效期天数，默认 3650",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if bool(args.admin_username) != bool(args.admin_phone):
        raise SystemExit("--admin-username 和 --admin-phone 必须同时提供")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        print("Seeding roles and permissions...")
        seed_roles(db)
        print("Seeding strategy templates...")
        seed_templates(db)
        print("Seeding system parameters...")
        seed_params(db)

        if args.admin_username:
            password = getpass.getpass("请输入管理员密码（至少 8 位）：")
            if len(password) < 8:
                raise SystemExit("管理员密码长度不能少于 8 位")
            print("Creating administrator account...")
            create_admin(
                db,
                username=args.admin_username,
                phone=args.admin_phone,
                password=password,
                expire_days=args.admin_expire_days,
            )

        db.commit()
        print("Database initialization completed.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
