"""
Add category to chats (Smart Chat Grouping — Task 027 Welle 1).

Revision ID: 2026_04_12_chats_category_smart_grouping
Revises: 2026_04_12_chat_auto_generated_title
"""

from alembic import op
import sqlalchemy as sa

revision = "2026_04_12_chats_category_smart_grouping"
down_revision = "2026_04_12_chat_auto_generated_title"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "chats",
        sa.Column(
            "category",
            sa.String(),
            nullable=False,
            server_default=sa.text("'general'"),
        ),
    )


def downgrade():
    op.drop_column("chats", "category")
