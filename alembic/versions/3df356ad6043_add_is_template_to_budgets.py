"""add_is_template_to_budgets

Revision ID: 3df356ad6043
Revises: af378577f847
Create Date: 2026-04-07 04:38:57.100887

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3df356ad6043"
down_revision: Union[str, None] = "af378577f847"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("budgets") as batch_op:
        batch_op.add_column(
            sa.Column("is_template", sa.Boolean(), server_default="false", nullable=False)
        )


def downgrade() -> None:
    with op.batch_alter_table("budgets") as batch_op:
        batch_op.drop_column("is_template")
