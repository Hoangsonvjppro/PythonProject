from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user, login_required
from models.models import db, User
from datetime import datetime, timedelta
import uuid

chatting = Blueprint('chatting', __name__)

# New models for forum-like features
class ChatRoom(db.Model):
    __tablename__ = 'chat_rooms'
    room_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_private = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    messages = db.relationship('Message', backref='room', lazy=True, cascade='all, delete-orphan')
    participants = db.relationship('RoomParticipant', backref='room', lazy=True, cascade='all, delete-orphan')

class RoomParticipant(db.Model):
    __tablename__ = 'room_participants'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(36), db.ForeignKey('chat_rooms.room_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('room_id', 'user_id', name='_room_user_uc'),)

class Message(db.Model):
    __tablename__ = 'messages'
    message_id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(36), db.ForeignKey('chat_rooms.room_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='messages')

class StatusPost(db.Model):
    __tablename__ = 'status_posts'
    post_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    comments = db.relationship('PostComment', backref='post', lazy=True, cascade='all, delete-orphan')
    user = db.relationship('User', backref='posts')

class PostComment(db.Model):
    __tablename__ = 'post_comments'
    comment_id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('status_posts.post_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='comments')

# Routes for chat community
@chatting.route('/chat')
@login_required
def chat_page():
    # Get public rooms and rooms the user is participating in
    public_rooms = ChatRoom.query.filter_by(is_private=False).all()
    
    user_rooms = db.session.query(ChatRoom).join(
        RoomParticipant, ChatRoom.room_id == RoomParticipant.room_id
    ).filter(
        RoomParticipant.user_id == current_user.id
    ).all()
    
    # Get recent status posts for the forum section
    recent_posts = StatusPost.query.order_by(StatusPost.created_at.desc()).limit(20).all()
    
    # Check if user has posted today
    today = datetime.utcnow().date()
    today_post = StatusPost.query.filter(
        StatusPost.user_id == current_user.id,
        StatusPost.created_at >= today
    ).first()
    can_post_today = today_post is None
    
    # Get user's comment count today
    today_comments_count = PostComment.query.filter(
        PostComment.user_id == current_user.id,
        PostComment.created_at >= today
    ).count()
    remaining_comments = max(0, 10 - today_comments_count)
    
    return render_template(
        'chatting.html',
        public_rooms=public_rooms,
        user_rooms=user_rooms,
        recent_posts=recent_posts,
        can_post_today=can_post_today,
        remaining_comments=remaining_comments
    )

@chatting.route('/chat/create-room', methods=['POST'])
@login_required
def create_room():
    name = request.form.get('room_name')
    description = request.form.get('room_description')
    is_private = 'is_private' in request.form
    
    if not name:
        flash('Room name is required', 'danger')
        return redirect(url_for('chatting.chat_page'))
    
    new_room = ChatRoom(
        name=name,
        description=description,
        is_private=is_private,
        created_by=current_user.id
    )
    db.session.add(new_room)
    
    # Add creator as participant
    participant = RoomParticipant(room_id=new_room.room_id, user_id=current_user.id)
    db.session.add(participant)
    
    db.session.commit()
    flash('Room created successfully', 'success')
    return redirect(url_for('chatting.room_detail', room_id=new_room.room_id))

@chatting.route('/chat/room/<room_id>')
@login_required
def room_detail(room_id):
    room = ChatRoom.query.get_or_404(room_id)
    
    # Check if private room and user is participant
    if room.is_private:
        participant = RoomParticipant.query.filter_by(
            room_id=room_id, user_id=current_user.id
        ).first()
        
        if not participant:
            flash('You do not have access to this room', 'danger')
            return redirect(url_for('chatting.chat_page'))
    
    # Get room messages
    messages = Message.query.filter_by(room_id=room_id).order_by(Message.timestamp).all()
    
    # Get room participants
    participants = db.session.query(User).join(
        RoomParticipant, User.id == RoomParticipant.user_id
    ).filter(
        RoomParticipant.room_id == room_id
    ).all()
    
    return render_template(
        'chat_room.html',
        room=room,
        messages=messages,
        participants=participants
    )

@chatting.route('/chat/join-room/<room_id>')
@login_required
def join_room_route(room_id):
    room = ChatRoom.query.get_or_404(room_id)
    
    # Check if user is already a participant
    participant = RoomParticipant.query.filter_by(
        room_id=room_id, user_id=current_user.id
    ).first()
    
    if not participant:
        if room.is_private:
            flash('This is a private room, you need an invitation', 'danger')
            return redirect(url_for('chatting.chat_page'))
        
        new_participant = RoomParticipant(room_id=room_id, user_id=current_user.id)
        db.session.add(new_participant)
        db.session.commit()
        flash('You have joined the room', 'success')
    
    return redirect(url_for('chatting.room_detail', room_id=room_id))

@chatting.route('/chat/new-post', methods=['POST'])
@login_required
def create_post():
    content = request.form.get('content')
    
    # Check if user has already posted today
    today = datetime.utcnow().date()
    today_post = StatusPost.query.filter(
        StatusPost.user_id == current_user.id,
        StatusPost.created_at >= today
    ).first()
    
    if today_post:
        flash('You can only create one post per day', 'danger')
        return redirect(url_for('chatting.chat_page'))
    
    if not content:
        flash('Post content cannot be empty', 'danger')
        return redirect(url_for('chatting.chat_page'))
    
    new_post = StatusPost(user_id=current_user.id, content=content)
    db.session.add(new_post)
    db.session.commit()
    
    flash('Post created successfully', 'success')
    return redirect(url_for('chatting.chat_page'))

@chatting.route('/chat/post/<post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    content = request.form.get('content')
    
    # Check if post exists
    post = StatusPost.query.get_or_404(post_id)
    
    # Check if user has reached daily comment limit
    today = datetime.utcnow().date()
    today_comments_count = PostComment.query.filter(
        PostComment.user_id == current_user.id,
        PostComment.created_at >= today
    ).count()
    
    if today_comments_count >= 10:
        flash('You have reached your daily comment limit (10)', 'danger')
        return redirect(url_for('chatting.chat_page'))
    
    if not content:
        flash('Comment content cannot be empty', 'danger')
        return redirect(url_for('chatting.chat_page'))
    
    new_comment = PostComment(
        post_id=post_id,
        user_id=current_user.id,
        content=content
    )
    db.session.add(new_comment)
    db.session.commit()
    
    flash('Comment added successfully', 'success')
    return redirect(url_for('chatting.chat_page'))

def register_socketio_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        if not current_user.is_authenticated:
            return False  # Reject connection if user is not authenticated
        print(f'User connected: {current_user.username}')

    @socketio.on('disconnect')
    def handle_disconnect():
        if current_user.is_authenticated:
            print(f'User disconnected: {current_user.username}')

    @socketio.on('join')
    def handle_join(data):
        if not current_user.is_authenticated:
            return
            
        room_id = data.get('room_id')
        if not room_id:
            return
        
        room = ChatRoom.query.get(room_id)
        if not room:
            emit('error', {'message': 'Room does not exist'})
            return
        
        if room.is_private:
            participant = RoomParticipant.query.filter_by(
                room_id=room_id, user_id=current_user.id
            ).first()
            
            if not participant:
                emit('error', {'message': 'You do not have access to this room'})
                return
        
        join_room(room_id)
        emit('user_joined', {
            'username': current_user.username,
            'avatar': current_user.avatar
        }, room=room_id)

    @socketio.on('leave')
    def handle_leave(data):
        if not current_user.is_authenticated:
            return
            
        room_id = data.get('room_id')
        if room_id:
            leave_room(room_id)
            emit('user_left', {
                'username': current_user.username
            }, room=room_id)

    @socketio.on('send_message')
    def handle_send_message(data):
        if not current_user.is_authenticated:
            emit('error', {'message': 'You must be logged in to send messages'})
            return
            
        room_id = data.get('room_id')
        message = data.get('message', '').strip()
        
        if not room_id or not message:
            return
        
        room = ChatRoom.query.get(room_id)
        if not room:
            emit('error', {'message': 'Room does not exist'})
            return
        
        if room.is_private:
            participant = RoomParticipant.query.filter_by(
                room_id=room_id, user_id=current_user.id
            ).first()
            
            if not participant:
                emit('error', {'message': 'You do not have access to this room'})
                return
        
        new_message = Message(
            room_id=room_id,
            user_id=current_user.id,
            content=message
        )
        db.session.add(new_message)
        db.session.commit()
        
        emit('new_message', {
            'username': current_user.username,
            'avatar': current_user.avatar,
            'message': message,
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }, room=room_id)

    @socketio.on('update_username')
    def handle_update_username(data):
        new_username = data.get('username', '').strip()
        
        if not new_username:
            return
        
        if current_user.is_authenticated:
            old_username = current_user.username
            if new_username != old_username:
                # Check if username is already taken
                existing_user = User.query.filter_by(username=new_username).first()
                if existing_user and existing_user.id != current_user.id:
                    emit('error', {'message': 'Username already taken'})
                    return
                
                current_user.username = new_username
                db.session.commit()
                emit('username_updated', {
                    'old_username': old_username,
                    'new_username': new_username
                }, broadcast=True)
        else:
            emit('error', {'message': 'Guests cannot change username'})

