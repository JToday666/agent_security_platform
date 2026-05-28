"""数据集公开可见性规则。"""

from __future__ import annotations

from sqlalchemy import and_

INTERNAL_FIXTURE_DATASET_PREFIXES = ("pytest_",)


def public_dataset_code_filter(column):
    """返回 SQL 条件，排除不应出现在用户侧链路中的夹具数据集。"""
    return and_(
        *(
            column.not_like(f"{prefix}%")
            for prefix in INTERNAL_FIXTURE_DATASET_PREFIXES
        )
    )
