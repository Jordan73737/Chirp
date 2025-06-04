# socket_events.py
from flask_socketio import emit
from app import socketio, db
from app.models import Message
from flask_socketio import emit, join_room
from app import socketio
from flask import request
from app.models import Message, db


connected_users = set()

@socketio.on('join')
def on_join(user_id):
    join_room(str(user_id))
    connected_users.add(user_id)
    emit('user_status', {'user_id': user_id, 'status': 'online'}, broadcast=True)


@socketio.on('disconnect')
def on_disconnect():
    # Need a way to track user_id from disconnect, maybe using session
    # Example (pseudo): user_id = session_user_id
    # connected_users.discard(user_id)
    # emit('user_status', {'user_id': user_id, 'status': 'offline'}, broadcast=True)
    pass


@socketio.on('send_message')
def handle_send_message(data):
    sender_id = data['sender_id']
    receiver_id = data['receiver_id']
    content = data['message']

    msg = Message(sender_id=sender_id, receiver_id=receiver_id, content=content)
    db.session.add(msg)
    db.session.commit()

    emit('receive_message', {
        'sender_id': sender_id,
        'content': content
    }, room=str(receiver_id))


@socketio.on('typing')
def handle_typing(data):
    emit('display_typing', {'from': data['from']}, room=str(data['to']))
