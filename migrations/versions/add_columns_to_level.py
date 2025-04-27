"""add columns to level model

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2023-06-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add missing columns to levels table
    op.add_column('levels', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('levels', sa.Column('icon', sa.String(length=50), nullable=True))
    op.add_column('levels', sa.Column('order', sa.Integer(), nullable=True, server_default='0'))


def downgrade():
    # Drop columns from levels table
    op.drop_column('levels', 'description')
    op.drop_column('levels', 'icon')
    op.drop_column('levels', 'order')
