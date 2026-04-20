"""数据集导入相关的数据库辅助函数。"""

from __future__ import annotations

import re

from sqlalchemy import text
from sqlalchemy.orm import Session


_SAFE_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")


def sync_pk_sequence(session: Session, table_name: str, column_name: str = "id") -> None:
    """将 PostgreSQL 自增序列对齐到表中的最大主键值。"""
    if not _SAFE_IDENTIFIER.fullmatch(table_name):
        raise ValueError(f"invalid table name: {table_name}")
    if not _SAFE_IDENTIFIER.fullmatch(column_name):
        raise ValueError(f"invalid column name: {column_name}")

    session.execute(
        text(
            f"""
            SELECT setval(
                pg_get_serial_sequence('{table_name}', '{column_name}'),
                COALESCE((SELECT MAX({column_name}) FROM {table_name}), 1),
                (SELECT MAX({column_name}) IS NOT NULL FROM {table_name})
            )
            """
        )
    )
