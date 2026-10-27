"""add image_url to announcement

Revision ID: 007_announcement_image
Revises: 006_backtest_data_source
Create Date: 2026-08-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007_announcement_image"
down_revision: Union[str, None] = "006_backtest_data_source"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "announcement",
        sa.Column("image_url", sa.String(255), nullable=True, comment="公告图片URL"),
    )


def downgrade() -> None:
    op.drop_column("announcement", "image_url")
