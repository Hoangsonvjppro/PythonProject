"""Add chat room management models

Revision ID: room_management_models
Revises: 
Create Date: 2023-11-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'room_management_models'
down_revision = None  # Thay đổi nếu cần
branch_labels = None
depends_on = None


def upgrade():
    # ChatRoom model
    op.create_table(
        'chat_rooms',
        sa.Column('room_id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_private', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False)
    )
    
    # RoomParticipant model
    op.create_table(
        'room_participants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('room_id', sa.String(36), sa.ForeignKey('chat_rooms.room_id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('joined_at', sa.DateTime(), default=datetime.utcnow),
        sa.UniqueConstraint('room_id', 'user_id', name='_room_user_uc')
    )
    
    # Message model
    op.create_table(
        'messages',
        sa.Column('message_id', sa.Integer(), primary_key=True),
        sa.Column('room_id', sa.String(36), sa.ForeignKey('chat_rooms.room_id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), default=datetime.utcnow)
    )
    
    # StatusPost model
    op.create_table(
        'status_posts',
        sa.Column('post_id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow)
    )
    
    # PostComment model
    op.create_table(
        'post_comments',
        sa.Column('comment_id', sa.Integer(), primary_key=True),
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('status_posts.post_id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow)
    )


def downgrade():
    op.drop_table('post_comments')
    op.drop_table('status_posts')
    op.drop_table('messages')
    op.drop_table('room_participants')
    op.drop_table('chat_rooms') 