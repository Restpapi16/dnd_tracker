"""refactor groups and remove enemies table

Revision ID: 003
Revises: 002
Create Date: 2026-02-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Добавляем новые поля в participants
    with op.batch_alter_table('participants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('count', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('hp_array', sa.Text(), nullable=True))
    
    # Удаляем таблицу enemies
    op.drop_table('enemies')


def downgrade():
    # Восстанавливаем таблицу enemies
    op.create_table('enemies',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('campaign_id', sa.INTEGER(), nullable=False),
        sa.Column('name', sa.VARCHAR(), nullable=False),
        sa.Column('max_hp', sa.INTEGER(), nullable=False),
        sa.Column('ac', sa.INTEGER(), nullable=False),
        sa.Column('initiative_modifier', sa.INTEGER(), nullable=False),
        sa.Column('attacks', sa.TEXT(), nullable=True),
        sa.Column('created_at', sa.DATETIME(), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_enemies_campaign_id'), 'enemies', ['campaign_id'], unique=False)
    
    # Удаляем новые поля из participants
    with op.batch_alter_table('participants', schema=None) as batch_op:
        batch_op.drop_column('hp_array')
        batch_op.drop_column('count')
