from flask_socketio import emit, join_room
from app import socketio, db
from flask import request
from app.models import Message, Notification, User

# This set keeps track of currently connected users (not persistent, resets on server restart)
connected_users = set()

# Log that the socket event handlers have been registered when the file is loaded
print("Socket event handlers registered")


# when user joins (connects to the socket), this runs
@socketio.on('join')
def on_join(users_id):
    # Put this user into a private room based on their user ID
    join_room(f"user_{users_id}")  # to emit messages specifically to this user later
    connected_users.add(users_id)

    # Let all users know that this user is now online
    emit('user_status', {'user_id': users_id, 'status': 'online'}, broadcast=True)


# when a user disconnects from the socket (e.g., closes tab), this runs
@socketio.on('disconnect')
def on_disconnect():
    pass


# handles when a user sends a chat message
@socketio.on("send_message")
def handle_send_message(data):
    print("Received message:", data)

    # Extract the sender ID, recipient ID, and content from the incoming data
    sender_id = data.get("sender_id")
    recipient_id = data.get("recipient_id")
    content = data.get("content")

    # Log the values to debug what's coming in
    print(f"senderId: {sender_id}")
    print(f"recipient_id: {recipient_id}")
    print(f"content: {content}")

    # Make sure none of the required fields are missing
    if not sender_id or not recipient_id or not content:
        return  # Stop if data is invalid

    # Get the sender's user object 
    sender = User.query.get(sender_id)

    # Create and store the new message in the database
    message = Message(sender_id=sender_id, receiver_id=recipient_id, content=content)
    db.session.add(message)
    db.session.commit()
    print(f"Saved message: {message.content} from {sender_id} to {recipient_id}")

    # Create a notification for recipient 
    notif = Notification(
        user_id=recipient_id,
        type='message',
        content=f"New message from {sender.username}",  
        link=f"/messages?user_id={sender_id}"  
    )
    db.session.add(notif)
    db.session.commit()

    # emits the message to the recipient (via their private room)
    emit("receive_message", {
        "sender_id": sender_id,
        "recipient_id": recipient_id,
        "content": content,
        "timestamp": message.timestamp.strftime("%H:%M"),
        "status": "sent",
    }, room=f"user_{recipient_id}")

    # also emits the message back to the sender so their chat updates instantly
    emit("receive_message", {
        "sender_id": sender_id,
        "recipient_id": recipient_id,
        "content": content,
        "timestamp": message.timestamp.strftime("%H:%M"),
        "status": "sent",
    }, room=f"user_{sender_id}")


# real time typing signifier 
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

    # Find all unread messages sent to the receiver
    messages = Message.query.filter_by(sender_id=sender_id, receiver_id=receiver_id, read=False).all()

    # Mark each one as read
    for msg in messages:
        msg.read = True
    db.session.commit()

    # tell the original sender that their messages were read
    emit('messages_marked_read', {'from': sender_id}, room=str(sender_id))


# test route to debug if emitting works
@socketio.on('test_message')
def handle_test_message(data):
    print("Got message:", data)
