"""add source_budget_id to budgets

Revision ID: af378577f847
Revises: b56f8d457ae1
Create Date: 2026-04-07 04:09:14.760698

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "af378577f847"
down_revision: Union[str, None] = "b56f8d457ae1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("budgets", sa.Column("source_budget_id", sa.UUID(), nullable=True))
    with op.batch_alter_table("budgets") as batch_op:
        batch_op.create_foreign_key(
            "fk_budgets_source_budget_id",
            "budgets",
            ["source_budget_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("budgets") as batch_op:
        batch_op.drop_constraint("fk_budgets_source_budget_id", type_="foreignkey")
    op.drop_column("budgets", "source_budget_id")
