"""fix_is_template_default

Revision ID: b6eb81408be5
Revises: 3df356ad6043
Create Date: 2026-04-07 06:01:56.575360

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b6eb81408be5"
down_revision: Union[str, None] = "3df356ad6043"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ensure is_template DEFAULT is the boolean false."""
    with op.batch_alter_table("budgets") as batch_op:
        batch_op.alter_column(
            "is_template",
            existing_type=sa.Boolean(),
            server_default=sa.text("false"),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Revert is_template DEFAULT back to string 'false'."""
    with op.batch_alter_table("budgets") as batch_op:
        batch_op.alter_column(
            "is_template",
            existing_type=sa.Boolean(),
            server_default="false",
            existing_nullable=False,
        )
