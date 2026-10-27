"""split SMTP sender config into system_param

Revision ID: 004_email_smtp_split
Revises: 003_email_config_push_status
Create Date: 2026-08-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004_email_smtp_split"
down_revision: Union[str, None] = "003_email_config_push_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("email_config", "smtp_host")
    op.drop_column("email_config", "smtp_port")
    op.drop_column("email_config", "smtp_user")
    op.drop_column("email_config", "smtp_password")
    op.drop_column("email_config", "from_email")


def downgrade() -> None:
    op.add_column("email_config", sa.Column("from_email", sa.String(128), nullable=False, server_default=""))
    op.add_column("email_config", sa.Column("smtp_password", sa.String(255), nullable=False, server_default=""))
    op.add_column("email_config", sa.Column("smtp_user", sa.String(128), nullable=False, server_default=""))
    op.add_column("email_config", sa.Column("smtp_port", sa.Integer(), nullable=False, server_default="465"))
    op.add_column("email_config", sa.Column("smtp_host", sa.String(128), nullable=False, server_default=""))
