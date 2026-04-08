"""add_run_datasets_and_control_fields

Revision ID: 7b1c9d2e4f6a
Revises: 518e3fcaca88
Create Date: 2026-04-09 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7b1c9d2e4f6a"
down_revision: Union[str, Sequence[str], None] = "518e3fcaca88"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    duplicate_codes = connection.execute(
        sa.text(
            """
            SELECT code
            FROM risk_subtypes
            GROUP BY code
            HAVING COUNT(*) > 1
            """
        )
    ).fetchall()
    if duplicate_codes:
        duplicated = ", ".join(code for (code,) in duplicate_codes)
        raise RuntimeError(f"risk_subtypes.code contains duplicates: {duplicated}")

    op.create_unique_constraint(op.f("uq_risk_subtypes_code"), "risk_subtypes", ["code"])

    op.create_table(
        "run_datasets",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("dataset_code", sa.Text(), nullable=False),
        sa.Column("dataset_name", sa.Text(), nullable=False),
        sa.Column("order_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("total_samples", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("completed_samples", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["test_runs.id"], name=op.f("fk_run_datasets_run_id_test_runs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_run_datasets")),
        sa.UniqueConstraint("run_id", "dataset_code", name=op.f("uq_run_datasets_run_id")),
    )
    op.create_index(op.f("ix_run_datasets_run_id"), "run_datasets", ["run_id"], unique=False)
    op.create_index(op.f("ix_run_datasets_dataset_code"), "run_datasets", ["dataset_code"], unique=False)
    op.create_index(op.f("ix_run_datasets_status"), "run_datasets", ["status"], unique=False)
    op.create_index("ix_run_datasets_run_id_status", "run_datasets", ["run_id", "status"], unique=False)

    op.add_column(
        "test_runs",
        sa.Column("pause_used", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column("test_runs", sa.Column("pause_deadline_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("test_runs", sa.Column("requested_action", sa.Text(), nullable=True))
    op.add_column("test_runs", sa.Column("requested_action_at", sa.DateTime(timezone=True), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE test_runs
            SET status = CASE status
                WHEN 'executing' THEN 'running'
                WHEN 'finished_success' THEN 'completed'
                WHEN 'finished_error' THEN 'failed'
                WHEN 'cancelled' THEN 'canceled'
                ELSE status
            END
            """
        )
    )


def downgrade() -> None:
    op.drop_column("test_runs", "requested_action_at")
    op.drop_column("test_runs", "requested_action")
    op.drop_column("test_runs", "pause_deadline_at")
    op.drop_column("test_runs", "pause_used")

    op.drop_index("ix_run_datasets_run_id_status", table_name="run_datasets")
    op.drop_index(op.f("ix_run_datasets_status"), table_name="run_datasets")
    op.drop_index(op.f("ix_run_datasets_dataset_code"), table_name="run_datasets")
    op.drop_index(op.f("ix_run_datasets_run_id"), table_name="run_datasets")
    op.drop_table("run_datasets")

    op.drop_constraint(op.f("uq_risk_subtypes_code"), "risk_subtypes", type_="unique")
