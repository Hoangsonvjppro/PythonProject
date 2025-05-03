from flask import render_template, request, jsonify, redirect, url_for, flash, abort
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user, login_required
from app.models.user import User
from app.models.chat import ChatRoom, RoomParticipant, Message, StatusPost, Comment
from app.extensions import db, socketio
from datetime import datetime, timedelta
from functools import wraps
import uuid
from app.chat import bp


# Decorator kiểm tra quyền chủ phòng
def room_owner_required(f):
    @wraps(f)
    def decorated_function(room_id, *args, **kwargs):
        room = ChatRoom.query.get_or_404(room_id)
        if not room.is_owner(current_user.id):
            flash('Bạn không phải là chủ phòng này', 'danger')
            return redirect(url_for('chat.room_detail', room_id=room_id))
        return f(room_id, *args, **kwargs)

    return decorated_function


# Routes for chat community
@bp.route('/')
@login_required
def index():
    return chat_page()


@bp.route('/')
@login_required
def chat_page():
    # Get public rooms and rooms the user is participating in
    public_rooms = ChatRoom.query.filter_by(is_private=False).all()
    
    # Get rooms the user is participating in (including private rooms)
    # Use a join to ensure we only get rooms that exist
    user_rooms = db.session.query(ChatRoom).join(
        RoomParticipant, ChatRoom.id == RoomParticipant.room_id
    ).filter(
        RoomParticipant.user_id == current_user.id
    ).all()
    
    # Get rooms owned by the user, excluding any that might be deleted
    owned_rooms = ChatRoom.query.filter_by(owner_id=current_user.id).all()
    
    # Get forum posts
    posts = StatusPost.query.order_by(StatusPost.created_at.desc()).limit(10).all()
    
    # Check if user can post today
    today = datetime.utcnow().date()
    today_post = StatusPost.query.filter(
        StatusPost.user_id == current_user.id,
        StatusPost.created_at >= today
    ).first()
    can_post_today = not today_post
    
    # Check remaining comments for today
    today_comments_count = Comment.query.filter(
        Comment.user_id == current_user.id,
        Comment.created_at >= today
    ).count()
    remaining_comments = max(0, 10 - today_comments_count)
    
    return render_template(
        'chat/index.html',
        public_rooms=public_rooms,
        user_rooms=user_rooms,
        owned_rooms=owned_rooms,
        posts=posts,
        can_post_today=can_post_today,
        remaining_comments=remaining_comments
    )


@bp.route('/create-room', methods=['POST'])
@login_required
def create_room():
    name = request.form.get('room_name')
    description = request.form.get('room_description')
    is_private = 'is_private' in request.form

    if not name:
        flash('Room name is required', 'danger')
        return redirect(url_for('chat.chat_page'))
        
    # Check for duplicate room names
    existing_room = ChatRoom.query.filter_by(name=name).first()
    if existing_room:
        flash('A room with this name already exists. Please choose a different name.', 'danger')
        return redirect(url_for('chat.chat_page'))

    # Tạo room_id trước khi tạo ChatRoom
    room_id = str(uuid.uuid4())

    new_room = ChatRoom(
        id=room_id,
        name=name,
        description=description,
        is_private=is_private,
        owner_id=current_user.id
    )
    db.session.add(new_room)

    # Commit trước để lưu ChatRoom và room_id
    db.session.commit()

    # Sau đó thêm participant với room_id đã có
    participant = RoomParticipant(room_id=room_id, user_id=current_user.id)
    db.session.add(participant)
    db.session.commit()

    flash('Room created successfully', 'success')
    return redirect(url_for('chat.room_detail', room_id=room_id))


@bp.route('/room/<room_id>')
@login_required
def room_detail(room_id):
    room = ChatRoom.query.get(room_id)
    if not room:
        flash('The room you are trying to access does not exist or has been deleted.', 'warning')
        return redirect(url_for('chat.chat_page'))

    # Check if private room and user is participant
    if room.is_private:
        participant = RoomParticipant.query.filter_by(
            room_id=room_id, user_id=current_user.id
        ).first()

        if not participant:
            flash('You do not have access to this room', 'danger')
            return redirect(url_for('chat.chat_page'))

    # Get room messages
    messages = Message.query.filter_by(room_id=room_id).order_by(Message.created_at).all()

    # Get room participants
    participants = db.session.query(User).join(
        RoomParticipant, User.id == RoomParticipant.user_id
    ).filter(
        RoomParticipant.room_id == room_id
    ).all()

    # Kiểm tra người dùng hiện tại có phải là chủ phòng không
    is_owner = room.is_owner(current_user.id)

    return render_template(
        'chat/room.html',
        room=room,
        messages=messages,
        participants=participants,
        is_owner=is_owner
    )


@bp.route('/join-room/<room_id>')
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
            return redirect(url_for('chat.chat_page'))

        new_participant = RoomParticipant(room_id=room_id, user_id=current_user.id)
        db.session.add(new_participant)
        db.session.commit()
        flash('You have joined the room', 'success')

    return redirect(url_for('chat.room_detail', room_id=room_id))


@bp.route('/new-post', methods=['POST'])
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
        return redirect(url_for('chat.chat_page'))

    if not content:
        flash('Post content cannot be empty', 'danger')
        return redirect(url_for('chat.chat_page'))

    new_post = StatusPost(user_id=current_user.id, content=content)
    db.session.add(new_post)
    db.session.commit()

    flash('Post created successfully', 'success')
    return redirect(url_for('chat.chat_page'))


@bp.route('/post/<post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    content = request.form.get('content')

    # Check if post exists
    post = StatusPost.query.get_or_404(post_id)

    # Check if user has reached daily comment limit
    today = datetime.utcnow().date()
    today_comments_count = Comment.query.filter(
        Comment.user_id == current_user.id,
        Comment.created_at >= today
    ).count()

    if today_comments_count >= 10:
        flash('You have reached your daily comment limit (10)', 'danger')
        return redirect(url_for('chat.chat_page'))

    if not content:
        flash('Comment content cannot be empty', 'danger')
        return redirect(url_for('chat.chat_page'))

    new_comment = Comment(
        post_id=post_id,
        user_id=current_user.id,
        content=content
    )
    db.session.add(new_comment)
    db.session.commit()

    flash('Comment added successfully', 'success')
    return redirect(url_for('chat.chat_page'))


@bp.route('/edit-room/<room_id>', methods=['GET', 'POST'])
@login_required
@room_owner_required
def edit_room(room_id):
    room = ChatRoom.query.get_or_404(room_id)

    if request.method == 'POST':
        name = request.form.get('room_name')
        description = request.form.get('room_description')
        is_private = 'is_private' in request.form

        if not name:
            flash('Room name is required', 'danger')
            return redirect(url_for('chat.edit_room', room_id=room_id))

        room.name = name
        room.description = description
        room.is_private = is_private

        db.session.commit()
        flash('Room updated successfully', 'success')
        return redirect(url_for('chat.room_detail', room_id=room_id))

    return render_template('chat/edit_room.html', room=room)


@bp.route('/delete-room/<room_id>', methods=['POST'])
@login_required
@room_owner_required
def delete_room(room_id):
    room = ChatRoom.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()

    flash('Room deleted successfully', 'success')
    return redirect(url_for('chat.chat_page'))


@bp.route('/invite-user/<room_id>', methods=['POST'])
@login_required
@room_owner_required
def invite_user(room_id):
    username = request.form.get('username')

    if not username:
        flash('Username is required', 'danger')
        return redirect(url_for('chat.room_detail', room_id=room_id))

    user = User.query.filter_by(username=username).first()

    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('chat.room_detail', room_id=room_id))

    # Check if user is already a participant
    participant = RoomParticipant.query.filter_by(
        room_id=room_id, user_id=user.id
    ).first()

    if participant:
        flash('User is already a participant', 'info')
        return redirect(url_for('chat.room_detail', room_id=room_id))

    new_participant = RoomParticipant(room_id=room_id, user_id=user.id)
    db.session.add(new_participant)
    db.session.commit()

    flash(f'{username} has been invited to the room', 'success')
    return redirect(url_for('chat.room_detail', room_id=room_id))


@bp.route('/remove-user/<room_id>/<user_id>', methods=['POST'])
@login_required
@room_owner_required
def remove_user(room_id, user_id):
    user_id = int(user_id)

    # Không thể xóa chủ phòng
    room = ChatRoom.query.get_or_404(room_id)
    if room.owner_id == user_id:
        flash('Cannot remove the room owner', 'danger')
        return redirect(url_for('chat.room_detail', room_id=room_id))

    participant = RoomParticipant.query.filter_by(
        room_id=room_id, user_id=user_id
    ).first_or_404()

    db.session.delete(participant)
    db.session.commit()

    flash('User has been removed from the room', 'success')
    return redirect(url_for('chat.room_detail', room_id=room_id))


@bp.route('/leave-room/<room_id>', methods=['POST'])
@login_required
def leave_room_route(room_id):
    room = ChatRoom.query.get_or_404(room_id)

    # Không thể rời khỏi phòng nếu là chủ phòng
    if room.owner_id == current_user.id:
        flash('Room owner cannot leave. Delete the room instead.', 'danger')
        return redirect(url_for('chat.room_detail', room_id=room_id))

    participant = RoomParticipant.query.filter_by(
        room_id=room_id, user_id=current_user.id
    ).first_or_404()

    db.session.delete(participant)
    db.session.commit()

    flash('You have left the room', 'success')
    return redirect(url_for('chat.chat_page'))


# SocketIO event handlers
def register_socketio_handlers():
    @socketio.on('connect')
    def handle_connect():
        if current_user.is_authenticated:
            print(f'Client connected: {current_user.username}')
        else:
            print('Anonymous client connected')

    @socketio.on('disconnect')
    def handle_disconnect():
        if current_user.is_authenticated:
            print(f'Client disconnected: {current_user.username}')
        else:
            print('Anonymous client disconnected')

    @socketio.on('join')
    def handle_join(data):
        print(f"Join event received: {data}")
        if not current_user.is_authenticated:
            print("Join rejected: User not authenticated")
            emit('error', {'message': 'You need to be logged in'})
            return False

        room_id = data.get('room_id')
        if not room_id:
            print(f"Join rejected: Missing room_id in data: {data}")
            emit('error', {'message': 'Room ID is required'})
            return False

        # Verify room exists and user has access
        room = ChatRoom.query.get(room_id)
        if not room:
            print(f"Join rejected: Room {room_id} not found or deleted")
            emit('error', {'message': 'Room does not exist or has been deleted'})
            return False

        if room.is_private:
            # Check if user is a participant
            is_participant = RoomParticipant.query.filter_by(
                room_id=room_id, user_id=current_user.id
            ).first()
            if not is_participant:
                print(f"Join rejected: User {current_user.username} not a participant in private room {room_id}")
                emit('error', {'message': 'You do not have access to this room'})
                return False

        # Join socketio room
        join_room(room_id)
        print(f"User {current_user.username} joined room {room_id}")

        # Notify other users
        emit('user_joined', {
            'username': current_user.username,
            'avatar': current_user.avatar or 'default.jpg'
        }, to=room_id, include_self=False)

        return True

    @socketio.on('leave')
    def handle_leave(data):
        if not current_user.is_authenticated:
            return False

        room_id = data.get('room_id')
        if not room_id:
            print(f"Leave rejected: Missing room_id in data: {data}")
            return False

        # Verify room exists
        room = ChatRoom.query.get(room_id)
        if not room:
            print(f"Leave rejected: Room {room_id} not found")
            return False

        # Leave socketio room
        leave_room(room_id)
        print(f"User {current_user.username} left room {room_id}")

        # Notify other users
        emit('user_left', {
            'username': current_user.username
        }, to=room_id)

        return True

    @socketio.on('send_message')
    def handle_send_message(data):
        print(f"Message event received: {data}")
        if not current_user.is_authenticated:
            print(f"Message rejected: User not authenticated")
            emit('error', {'message': 'You need to be logged in'})
            return False

        room_id = data.get('room_id')
        message_text = data.get('message')

        if not room_id or not message_text:
            print(f"Message rejected: Invalid data: {data}")
            emit('error', {'message': 'Invalid data'})
            return False

        # Verify room exists and user has access
        room = ChatRoom.query.get(room_id)
        if not room:
            print(f"Message rejected: Room {room_id} not found or deleted")
            emit('error', {'message': 'Room does not exist or has been deleted'})
            return False

        if room.is_private:
            # Check if user is a participant
            is_participant = RoomParticipant.query.filter_by(
                room_id=room_id, user_id=current_user.id
            ).first()
            if not is_participant:
                print(f"Message rejected: User {current_user.username} not a participant in private room {room_id}")
                emit('error', {'message': 'You do not have access to this room'})
                return False

        # Save message to database
        new_message = Message(
            room_id=room_id,
            user_id=current_user.id,
            content=message_text
        )
        db.session.add(new_message)
        db.session.commit()

        # Broadcast message to room
        emit('new_message', {
            'id': new_message.id,
            'username': current_user.username,
            'avatar': current_user.avatar or 'default.jpg',
            'message': message_text,
            'timestamp': new_message.created_at.isoformat()
        }, to=room_id)

        print(f"Message from {current_user.username} sent to room {room_id}")
        return True

    @socketio.on('update_username')
    def handle_update_username(data):
        if not current_user.is_authenticated:
            return False

        room_id = data.get('room_id')
        if not room_id:
            return False

        # Notify room about username update
        emit('user_updated', {
            'user_id': current_user.id,
            'username': current_user.username,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)


# Register SocketIO handlers
register_socketio_handlers()