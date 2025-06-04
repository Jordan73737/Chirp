# socket_events.py
from flask_socketio import emit
from app import socketio, db
from app.models import Message

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
