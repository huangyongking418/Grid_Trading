"""add image_name to announcement

Revision ID: 008_announcement_image_name
Revises: 007_announcement_image
Create Date: 2026-08-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008_announcement_image_name"
down_revision: Union[str, None] = "007_announcement_image"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "announcement",
        sa.Column("image_name", sa.String(128), nullable=True, comment="公告图片名称"),
    )


def downgrade() -> None:
    op.drop_column("announcement", "image_name")
