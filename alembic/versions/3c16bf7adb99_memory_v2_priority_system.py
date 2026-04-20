"""memory_v2_priority_system

Revision ID: 3c16bf7adb99
Revises: a257f80a0f62
Create Date: 2026-04-06 17:33:28.949359

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '3c16bf7adb99'
down_revision: Union[str, Sequence[str], None] = 'a257f80a0f62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Memory System V2: Float Priority Migration."""
    
    # ─────────────────────────────────────────────
    # 1. Neue Spalten hinzufügen (mit Server-Defaults)
    # ─────────────────────────────────────────────
    
    with op.batch_alter_table('memories', schema=None) as batch_op:
        batch_op.add_column(sa.Column('priority', sa.Float(), server_default='0.5', nullable=False))
        batch_op.add_column(sa.Column('memory_type', sa.String(length=20), server_default='GENERAL', nullable=False))
        batch_op.add_column(sa.Column('ttl', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('tags', sa.JSON(), server_default='[]', nullable=True))
        batch_op.add_column(sa.Column('source_skill', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('user_editable', sa.Boolean(), server_default='1', nullable=False))
        batch_op.add_column(sa.Column('canonical_key', sa.String(length=255), nullable=True))
    
    # ─────────────────────────────────────────────
    # 2. Backfill: Priority aus core_priority ableiten
    # ─────────────────────────────────────────────
    
    conn = op.get_bind()
    conn.execute(text("""
        UPDATE memories 
        SET priority = CASE 
            WHEN core_priority = 2 THEN 0.95
            WHEN core_priority = 1 THEN 0.75
            WHEN is_core_fact = 1 THEN 0.70
            WHEN expires_at IS NOT NULL THEN 0.60
            ELSE 0.50
        END
    """))
    
    # ─────────────────────────────────────────────
    # 3. Backfill: memory_type ableiten
    # ─────────────────────────────────────────────
    
    conn.execute(text("""
        UPDATE memories 
        SET memory_type = CASE 
            WHEN core_priority >= 1 THEN 'CORE'
            WHEN expires_at IS NOT NULL THEN 'TEMPORAL'
            ELSE 'GENERAL'
        END
    """))
    
    # ─────────────────────────────────────────────
    # 4. Backfill: canonical_key aus snippet JSON extrahieren
    # ─────────────────────────────────────────────
    
    conn.execute(text("""
        UPDATE memories 
        SET canonical_key = COALESCE(
            json_extract(snippet, '$.canonical_key'),
            json_extract(snippet, '$.key'),
            text_hash
        )
        WHERE snippet IS NOT NULL AND snippet LIKE '%{%}%'
    """))
    
    # ─────────────────────────────────────────────
    # 5. Backfill: tags aus category ableiten
    # ─────────────────────────────────────────────
    
    category_tags = [
        ('Physis', '["appearance", "identity"]'),
        ('Stil', '["fashion", "identity"]'),
        ('Haustier-Details', '["pet", "identity"]'),
        ('Beziehungen', '["contact", "social"]'),
        ('Termine', '["calendar", "temporal"]'),
        ('Gesundheit', '["health", "medical"]'),
        ('Beruf', '["professional", "career"]'),
        ('Vorlieben', '["preferences", "personal"]'),
    ]
    
    for cat, tags_json in category_tags:
        conn.execute(text(f"""
            UPDATE memories 
            SET tags = '{tags_json}'
            WHERE category = '{cat}' AND (tags IS NULL OR tags = '[]')
        """))
    
    # ─────────────────────────────────────────────
    # 6. Indices erstellen
    # ─────────────────────────────────────────────
    
    # SQLite partial indexes via create_index with sqlite_where
    op.create_index('idx_priority_high', 'memories', ['priority'], 
                    sqlite_where=text('priority >= 0.8'))
    op.create_index('idx_chat_priority', 'memories', ['chat_id', sa.text('priority DESC')])
    op.create_index('idx_expires_at', 'memories', ['expires_at'], 
                    sqlite_where=text('expires_at IS NOT NULL'))
    op.create_index('idx_source_skill', 'memories', ['source_skill'],
                    sqlite_where=text('source_skill IS NOT NULL'))
    
    # ─────────────────────────────────────────────
    # 7. Default source_skill setzen
    # ─────────────────────────────────────────────
    
    conn.execute(text("""
        UPDATE memories 
        SET source_skill = 'system.legacy_migration'
        WHERE source_skill IS NULL
    """))


def downgrade() -> None:
    """Downgrade schema - Reverse Migration."""
    
    # Indices zuerst droppen
    op.drop_index('idx_source_skill', table_name='memories')
    op.drop_index('idx_expires_at', table_name='memories')
    op.drop_index('idx_chat_priority', table_name='memories')
    op.drop_index('idx_priority_high', table_name='memories')
    
    # Spalten droppen
    with op.batch_alter_table('memories', schema=None) as batch_op:
        batch_op.drop_column('canonical_key')
        batch_op.drop_column('user_editable')
        batch_op.drop_column('source_skill')
        batch_op.drop_column('tags')
        batch_op.drop_column('ttl')
        batch_op.drop_column('memory_type')
        batch_op.drop_column('priority')
