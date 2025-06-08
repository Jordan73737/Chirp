from flask_socketio import emit, join_room
from app import socketio, db
from flask import request
from app.models import Message, Notification, User

connected_users = set()
print("Socket event handlers registered")
@socketio.on('join')
def on_join(users_id):
    join_room(f"user_{users_id}") 
    connected_users.add(users_id)
    emit('user_status', {'user_id': users_id, 'status': 'online'}, broadcast=True)


@socketio.on('disconnect')
def on_disconnect():
    # Full presence tracking would require user ID tracking via session or token
    pass

@socketio.on("send_message")
def handle_send_message(data):
    print("Received message:", data)
    sender_id = data.get("sender_id")
    recipient_id = data.get("recipient_id")
    content = data.get("content")

    print(f"senderId: {sender_id}")
    print(f"recipient_id: {recipient_id}")
    print(f"content: {content}")
    if not sender_id or not recipient_id or not content:
            return 
    if sender_id and recipient_id and content:
        # Fetch the sender user from DB (needed for the notification text)
        sender = User.query.get(sender_id)

        # Save the message to DB
        message = Message(sender_id=sender_id, receiver_id=recipient_id, content=content)
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


@socketio.on('test_message')
def handle_test_message(data):
    print("Got message:", data)