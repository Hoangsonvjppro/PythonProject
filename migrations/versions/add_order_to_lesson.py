"""add order column to lesson model

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2023-06-01 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6g7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Add order column to lessons table
    op.add_column('lessons', sa.Column('order', sa.Integer(), nullable=True, server_default='0'))


def downgrade():
    # Drop order column from lessons table
    op.drop_column('lessons', 'order')
