"""google_oauth_user_and_refresh_tokens

Revision ID: 9c9a764dc357
Revises: b6eb81408be5
Create Date: 2026-04-24 16:57:59.088691

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c9a764dc357'
down_revision: Union[str, None] = 'b6eb81408be5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "refresh_tokens",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), server_default=sa.text("(false)"), nullable=False),
        sa.Column("id", sa.UUID(), server_default=sa.text("(gen_random_uuid())"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("(true)"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_refresh_tokens_token_hash"), "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False)
    op.add_column("users", sa.Column("google_sub", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_users_google_sub"), "users", ["google_sub"], unique=True)
    op.drop_column("users", "password_hash")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("users", sa.Column("password_hash", sa.TEXT(), nullable=True))
    op.drop_index(op.f("ix_users_google_sub"), table_name="users")
    op.drop_column("users", "google_sub")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_token_hash"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
