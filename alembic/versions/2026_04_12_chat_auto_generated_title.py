"""
Add auto_generated and last_topic_hash to chats.

Revision ID: 2026_04_12_chat_auto_generated_title
Revises: 2026_04_06_add_change_history
"""

from alembic import op
import sqlalchemy as sa

revision = "2026_04_12_chat_auto_generated_title"
down_revision = "2026_04_06_add_change_history"
branch_labels = None
depends_on = None


def upgrade():
    # Bestehende Chats: kein automatisches Überschreiben (Variante A) → false.
    # Neu über ORM angelegte Chats setzen auto_generated=True explizit.
    op.add_column(
        "chats",
        sa.Column("auto_generated", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.add_column(
        "chats",
        sa.Column("last_topic_hash", sa.String(), nullable=True),
    )


def downgrade():
    op.drop_column("chats", "last_topic_hash")
    op.drop_column("chats", "auto_generated")
