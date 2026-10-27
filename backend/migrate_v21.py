# -*- coding: utf-8 -*-
"""
v2.1 数据库迁移：策略资金拆分与切分方式

新增字段（非破坏性）：
  strategy_instance: grid_funds / position_funds / split_mode / layer_shares
  grid_layer: layer_type

存量回填：
  grid_funds = total_funds, position_funds = 0, split_mode = 'amount'
  已有 grid_layer 全部标记为 layer_type = 'grid'

用法：在 backend 目录下执行  python migrate_v21.py
"""
from sqlalchemy import create_engine, inspect, text

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)


def add_column_if_missing(table: str, column_def: str) -> None:
    col_name = column_def.split()[0]
    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns(table)}
    if col_name in cols:
        print(f"  = {table}.{col_name} 已存在，跳过")
        return
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE `{table}` ADD COLUMN {column_def}"))
    print(f"  + {table}.{col_name} 已添加")


def main() -> None:
    print("=== v2.1 迁移开始 ===")
    add_column_if_missing("strategy_instance", "grid_funds FLOAT NOT NULL DEFAULT 0")
    add_column_if_missing("strategy_instance", "position_funds FLOAT NOT NULL DEFAULT 0")
    add_column_if_missing("strategy_instance", "split_mode VARCHAR(16) NOT NULL DEFAULT 'amount'")
    add_column_if_missing("strategy_instance", "layer_shares JSON NULL")
    add_column_if_missing("grid_layer", "layer_type VARCHAR(16) NOT NULL DEFAULT 'grid'")

    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE strategy_instance "
                "SET grid_funds = total_funds, position_funds = 0, split_mode = 'amount' "
                "WHERE grid_funds = 0 AND total_funds > 0"
            )
        )
        print("  存量策略回填完成：grid_funds = total_funds, position_funds = 0, split_mode = amount")
    print("=== v2.1 迁移完成 ===")


if __name__ == "__main__":
    main()
