from flask_socketio import emit, join_room
from app import socketio, db
from flask import request
from app.models import Message, Notification, User

connected_users = set()

@socketio.on('join')
def on_join(user_id):
    join_room(str(user_id))
    connected_users.add(user_id)
    emit('user_status', {'user_id': user_id, 'status': 'online'}, broadcast=True)

@socketio.on('disconnect')
def on_disconnect():
    # Full presence tracking would require user ID tracking via session or token
    pass

@socketio.on("send_message")
def handle_send_message(data):
    sender_id = data.get("sender_id")
    recipient_id = data.get("recipient_id")
    content = data.get("content")

    if not sender_id or not recipient_id or not content:
            return 
    if sender_id and recipient_id and content:
        # Fetch the sender user from DB (needed for the notification text)
        sender = User.query.get(sender_id)

        # Save the message to DB
        message = Message(sender_id=sender_id, recipient_id=recipient_id, content=content)
        db.session.add(message)
        db.session.commit()
        print(f"Saved message: {message.content} from {sender_id} to {recipient_id}")
        print(f"Saved message: {message.content}")

        # Save notification for the recipient
        notif = Notification(
            user_id=recipient_id,
            type='message',
            content=f"New message from {sender.username}",
            link=f"/messages?user_id={sender_id}"
        )
        db.session.add(notif)
        db.session.commit()

        # Emit the message to recipient
        emit("receive_message", {
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "content": content,
            "timestamp": message.timestamp.strftime("%H:%M"),
            "status": "sent",
        }, room=f"user_{recipient_id}")

        # Echo the message to sender too
        emit("receive_message", {
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "content": content,
            "timestamp": message.timestamp.strftime("%H:%M"),
            "status": "sent",
        }, room=f"user_{sender_id}")


@socketio.on('typing')
def handle_typing(data):
    emit('display_typing', {
        'from': data['from'],
        'username': data['username']
    }, room=str(data['to']))

@socketio.on('mark_read')
def handle_mark_read(data):
    sender_id = data['to']
    receiver_id = data['from']

    messages = Message.query.filter_by(sender_id=sender_id, receiver_id=receiver_id, read=False).all()
    for msg in messages:
        msg.read = True
    db.session.commit()

    emit('messages_marked_read', {'from': sender_id}, room=str(sender_id))


