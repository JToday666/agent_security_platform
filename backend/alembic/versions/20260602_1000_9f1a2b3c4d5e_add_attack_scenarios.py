"""add_attack_scenarios

Revision ID: 9f1a2b3c4d5e
Revises: a1b2c3d4e5f6
Create Date: 2026-06-02 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "9f1a2b3c4d5e"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PROMPT_RISK_DOMAINS = (
    "confidentiality",
    "integrity",
    "availability_and_destructive_harm",
)
ABUSE_RISK_DOMAINS = (
    "unauthorized_execution_and_system_control",
    "fraud_impersonation_and_social_engineering",
    "content_and_societal_harm",
    "harmful_search_and_reconnaissance",
)


def upgrade() -> None:
    translation_column_type = postgresql.JSONB(astext_type=sa.Text())
    op.create_table(
        "attack_scenarios",
        sa.Column("id", sa.SmallInteger(), primary_key=True, comment="攻击场景主键ID"),
        sa.Column("code", sa.Text(), nullable=False, comment="攻击场景唯一编码"),
        sa.Column("name", sa.Text(), nullable=False, comment="攻击场景展示名"),
        sa.Column("description", sa.Text(), nullable=True, comment="攻击场景说明"),
        sa.Column(
            "translations",
            translation_column_type,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="按 locale 存储的攻击场景展示字段翻译",
        ),
        sa.Column("sort_order", sa.SmallInteger(), nullable=True, comment="攻击场景展示排序"),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="是否启用",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="更新时间",
        ),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_attack_scenarios_code", "attack_scenarios", ["code"])
    op.create_index(
        "ix_attack_scenarios_sort_order", "attack_scenarios", ["sort_order"]
    )

    op.create_table(
        "attack_scenario_risk_domains",
        sa.Column(
            "attack_scenario_id",
            sa.SmallInteger(),
            sa.ForeignKey("attack_scenarios.id"),
            primary_key=True,
            comment="攻击场景ID",
        ),
        sa.Column(
            "risk_category_id",
            sa.SmallInteger(),
            sa.ForeignKey("risk_categories.id"),
            primary_key=True,
            comment="风险域ID",
        ),
        sa.Column("sort_order", sa.SmallInteger(), nullable=True, comment="该风险域在场景内的排序"),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="是否启用",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="创建时间",
        ),
        sa.UniqueConstraint("attack_scenario_id", "risk_category_id"),
    )
    op.create_index(
        "ix_attack_scenario_risk_domains_category_id",
        "attack_scenario_risk_domains",
        ["risk_category_id"],
    )

    op.add_column(
        "risk_subtypes",
        sa.Column(
            "attack_scenario_id",
            sa.SmallInteger(),
            nullable=True,
            comment="归属的攻击场景ID",
        ),
    )
    op.create_index(
        "ix_risk_subtypes_attack_scenario_id",
        "risk_subtypes",
        ["attack_scenario_id"],
    )
    op.create_foreign_key(
        "fk_risk_subtypes_attack_scenario_id_attack_scenarios",
        "risk_subtypes",
        "attack_scenarios",
        ["attack_scenario_id"],
        ["id"],
    )

    scenarios = [
        (
            1,
            "prompt_injection",
            "提示注入",
            "覆盖直接和间接提示注入攻击。",
            1,
        ),
        (
            2,
            "model_abuse_and_unauthorized_actions",
            "模型滥用与越权行为",
            "覆盖模型滥用、违规生成和越权操作。",
            2,
        ),
        (3, "knowledge_base_poisoning", "知识库投毒", "覆盖知识库污染与检索误导。", 3),
        (4, "tool_call_hijacking", "工具调用劫持", "覆盖工具调用参数和流程劫持。", 4),
    ]
    for scenario in scenarios:
        op.execute(
            sa.text(
                """
                INSERT INTO attack_scenarios
                    (id, code, name, description, sort_order, translations)
                VALUES
                    (:id, :code, :name, :description, :sort_order, '{}'::jsonb)
                ON CONFLICT (code) DO NOTHING
                """
            ).bindparams(
                id=scenario[0],
                code=scenario[1],
                name=scenario[2],
                description=scenario[3],
                sort_order=scenario[4],
            )
        )

    _seed_scenario_risk_domains("prompt_injection", PROMPT_RISK_DOMAINS)
    _seed_scenario_risk_domains(
        "model_abuse_and_unauthorized_actions", ABUSE_RISK_DOMAINS
    )
    _assign_existing_subtypes("prompt_injection", PROMPT_RISK_DOMAINS)
    _assign_existing_subtypes(
        "model_abuse_and_unauthorized_actions", ABUSE_RISK_DOMAINS
    )

    op.alter_column("risk_subtypes", "attack_scenario_id", nullable=False)


def downgrade() -> None:
    op.drop_constraint(
        "fk_risk_subtypes_attack_scenario_id_attack_scenarios",
        "risk_subtypes",
        type_="foreignkey",
    )
    op.drop_index("ix_risk_subtypes_attack_scenario_id", table_name="risk_subtypes")
    op.drop_column("risk_subtypes", "attack_scenario_id")
    op.drop_index(
        "ix_attack_scenario_risk_domains_category_id",
        table_name="attack_scenario_risk_domains",
    )
    op.drop_table("attack_scenario_risk_domains")
    op.drop_index("ix_attack_scenarios_sort_order", table_name="attack_scenarios")
    op.drop_index("ix_attack_scenarios_code", table_name="attack_scenarios")
    op.drop_table("attack_scenarios")


def _seed_scenario_risk_domains(scenario_code: str, risk_domain_codes: tuple[str, ...]) -> None:
    for index, risk_domain_code in enumerate(risk_domain_codes, start=1):
        op.execute(
            sa.text(
                """
                INSERT INTO attack_scenario_risk_domains
                    (attack_scenario_id, risk_category_id, sort_order)
                SELECT scenario.id, category.id, :sort_order
                FROM attack_scenarios scenario
                JOIN risk_categories category ON category.code = :risk_domain_code
                WHERE scenario.code = :scenario_code
                ON CONFLICT (attack_scenario_id, risk_category_id) DO NOTHING
                """
            ).bindparams(
                scenario_code=scenario_code,
                risk_domain_code=risk_domain_code,
                sort_order=index,
            )
        )


def _assign_existing_subtypes(
    scenario_code: str, risk_domain_codes: tuple[str, ...]
) -> None:
    op.execute(
        sa.text(
            """
            UPDATE risk_subtypes subtype
            SET attack_scenario_id = scenario.id
            FROM attack_scenarios scenario, risk_categories category
            WHERE subtype.category_id = category.id
              AND scenario.code = :scenario_code
              AND category.code IN :risk_domain_codes
            """
        )
        .bindparams(
            sa.bindparam("scenario_code"),
            sa.bindparam("risk_domain_codes", expanding=True),
        )
        .bindparams(
            scenario_code=scenario_code,
            risk_domain_codes=risk_domain_codes,
        )
    )
