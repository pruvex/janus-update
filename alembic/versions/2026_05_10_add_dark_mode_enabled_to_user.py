"""
Add dark_mode_enabled field to users table.

Revision ID: 2026_05_10_add_dark_mode_enabled_to_user
Revises: 2026_04_12_chats_category_smart_grouping
"""

from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = '2026_05_10_add_dark_mode_enabled_to_user'
down_revision = '2026_04_12_chats_category_smart_grouping'
branch_labels = None
depends_on = None


def upgrade():
    # Add dark_mode_enabled Boolean column with default True (Dark Mode)
    op.add_column('users', sa.Column('dark_mode_enabled', sa.Boolean, nullable=False, server_default='1'))


def downgrade():
    op.drop_column('users', 'dark_mode_enabled')
