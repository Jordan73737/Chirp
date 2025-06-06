from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from app.forms import RegisterForm, LoginForm, LikeForm, ProfileForm, PostForm, EmptyForm
from app import db, login_manager
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Post, Like, Profile, Friend, FriendRequest, Message, Notification
import os
from werkzeug.utils import secure_filename
from flask import current_app
from PIL import Image


# main is the type of route that we will use, which is of type BluePrint (in-built flask Blueprint)
main = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = ProfileForm()

    # Ensure profile exists for current user
    if not current_user.profile:
        current_user.profile = Profile(user_id=current_user.id)
        db.session.add(current_user.profile)
        db.session.commit()

    profile = current_user.profile # Profile is then guaranteed to exist after doing thr above


    if form.validate_on_submit():
        # Update standard profile fields
        profile.bio = form.bio.data
        profile.location = form.location.data
        profile.website = form.website.data

        # Get selected privacy level from form (radio buttons)
        selected_privacy = request.form.get('privacy_level')
        if selected_privacy is not None:
            profile.privacy_level = int(selected_privacy)

        db.session.commit()
        flash('Settings updated.', 'success')
        return redirect(url_for('main.settings'))

    # Pre-fill form fields
    form.bio.data = profile.bio
    form.location.data = profile.location
    form.website.data = profile.website

    return render_template('settings.html', form=form, profile=profile)


@main.route('/profile')
@login_required
def profile():
    form = EmptyForm()
    mutual_friends = set(current_user.friends).intersection(current_user.friend_of)
    return render_template(
        'profile.html',
        user=current_user,
        form=form,
        mutual_friends=mutual_friends,
        can_view_full_profile=True  
    )


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_and_save(image, filepath, max_size=(300, 300)):
    img = Image.open(image)
    img = img.convert("RGB")
    img.thumbnail(max_size)
    img.save(filepath, format='JPEG')

@main.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm()

    if form.validate_on_submit():
        if not current_user.profile:
            profile = Profile(user=current_user)
            db.session.add(profile)
        else:
            profile = current_user.profile

        profile.bio = form.bio.data
        profile.location = form.location.data
        profile.website = form.website.data

        if form.profile_pic.data:
            uploaded_file = form.profile_pic.data
            if allowed_file(uploaded_file.filename):
                filename = secure_filename(uploaded_file.filename)
                filepath = os.path.join(current_app.root_path, 'static/uploads', filename)
                resize_and_save(uploaded_file, filepath)
                profile.profile_pic = filename
            else:
                flash("Invalid file type. Please upload an image (jpg, png, gif).", "danger")
                return redirect(request.url)

        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('main.profile'))

    if request.method == 'GET' and current_user.profile:
        form.bio.data = current_user.profile.bio
        form.location.data = current_user.profile.location
        form.website.data = current_user.profile.website

    return render_template('edit_profile.html', form=form)

@main.route('/friend_request/send/<int:user_id>', methods=['POST'])
@login_required
def send_friend_request(user_id):
    user = User.query.get_or_404(user_id)

    if user_id == current_user.id:
        return "Cannot send request to yourself", 400

    existing_request = FriendRequest.query.filter_by(
        sender_id=current_user.id,
        receiver_id=user_id
    ).first()

    if not existing_request:
        new_request = FriendRequest(sender_id=current_user.id, receiver_id=user_id, status='pending')
        db.session.add(new_request)

        notif = Notification(
            user_id=user.id,
            type='friend_request',
            content=f"{current_user.username} sent you a friend request",
            link="/profile"
        )
        db.session.add(notif)

        db.session.commit()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template(
            '_friend_request_buttons.html',
            user=user,
            form=EmptyForm(),
            already_sent=True
        )

    return redirect(url_for('main.view_user', user_id=user_id))


@main.route('/cancel_friend_request/<int:user_id>', methods=['POST'])
@login_required
def cancel_friend_request(user_id):
    request_to_cancel = FriendRequest.query.filter_by(sender_id=current_user.id, receiver_id=user_id, status='pending').first()
    if request_to_cancel:
        db.session.delete(request_to_cancel)
        db.session.commit()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        user = User.query.get_or_404(user_id)
        return render_template('_friend_request_buttons.html', user=user, form=EmptyForm())
    return redirect(url_for('main.profile'))



@main.route('/friend_request/accept/<int:request_id>', methods=['POST'])
@login_required
def accept_friend_request(request_id):
    friend_request = FriendRequest.query.get_or_404(request_id)
    if friend_request.receiver_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for('main.profile'))

    # Accept and create friendship
    friend_request.status = 'accepted'
    db.session.add(Friend(user_id=friend_request.sender_id, friend_id=friend_request.receiver_id))
    db.session.add(Friend(user_id=friend_request.receiver_id, friend_id=friend_request.sender_id))
    db.session.commit()
    flash("Friend request accepted.", "success")
    return redirect(url_for('main.profile'))


@main.route('/friend_request/reject/<int:request_id>', methods=['POST'])
@login_required
def reject_friend_request(request_id):
    friend_request = FriendRequest.query.get_or_404(request_id)
    if friend_request.receiver_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for('main.profile'))

    friend_request.status = 'rejected'
    db.session.commit()
    flash("Friend request rejected.", "info")
    return redirect(url_for('main.profile'))

@main.route('/friend/unfriend/<int:user_id>', methods=['POST'])
@login_required
def unfriend(user_id):
    friend = User.query.get_or_404(user_id)

    if friend not in current_user.friends:
        return "Not friends", 400

    current_user.friends.remove(friend)
    friend.friends.remove(current_user)  # bidirectional removal
    db.session.commit()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template('_friend_request_buttons.html', user=friend, form=EmptyForm(), already_sent=False)
    return redirect(url_for('main.view_user', user_id=user_id))





@main.route('/')
def index():
    return redirect(url_for('main.register'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.feed'))

    form = RegisterForm()

    if request.method == 'POST':
        print("Form submitted")
        print(form.errors)
        print(f"request method: {request.method}")
        print(f"form submitted: {form.is_submitted()}")
        print("username:", form.username.data)
        print("email:", form.email.data)
        print(f"validate_on_submit(): {form.validate_on_submit()}")


    if form.validate_on_submit():
        print("Form validated!")              

        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists.', 'danger')
        elif User.query.filter_by(username=form.username.data).first():
            flash('Username already taken.', 'danger')
        else:
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('main.login'))

    return render_template('register.html', form=form)

    


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.feed'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('main.feed'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

@main.route('/feed', methods=['GET', 'POST'])
@login_required
def feed():
    form = PostForm()
    like_form = LikeForm()  # CSRF-protected like form

    if form.validate_on_submit():
        post = Post(content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('main.feed'))

    posts = Post.query.filter_by(parent_id=None).order_by(Post.timestamp.desc()).all()

    
    liked_post_ids = [like.post_id for like in current_user.likes]


    return render_template(
        'feed.html',
        user=current_user,
        form=form,
        like_form=like_form,
        posts=posts,
        liked_post_ids=liked_post_ids
    )


@main.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        flash("You can't edit this post.", 'danger')
        return redirect(url_for('main.feed'))

    form = PostForm()
    if form.validate_on_submit():
        post.content = form.content.data
        db.session.commit()
        flash('Post updated!', 'success')
        return redirect(url_for('main.feed'))
    elif request.method == 'GET':
        form.content.data = post.content

    return render_template('edit_post.html', form=form)


@main.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    post.deleted = True
    db.session.commit()
    flash('Post deleted', 'info')
    return redirect(url_for('main.feed'))




@main.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()

    if existing_like:
        db.session.delete(existing_like)
        flash('Like removed.', 'info')
    else:
        like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(like)
        flash('Post liked!', 'success')

    db.session.commit()
    return redirect(url_for('main.feed'))

@main.route('/user/<int:user_id>')
@login_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)

    # Ensure profile exists
    if not user.profile:
        user.profile = Profile(user_id=user.id)
        db.session.add(user.profile)
        db.session.commit()

    profile = user.profile
    form = ProfileForm()

    # Initialize flags
    can_view_full_profile = False
    already_sent = False
    is_friend = Friend.query.filter_by(user_id=current_user.id, friend_id=user.id).first()

    # Prevent sending requests to self
    if user.id == current_user.id:
        can_view_full_profile = True
    else:
        # Check if request already sent
        existing_request = FriendRequest.query.filter_by(
            sender_id=current_user.id,
            receiver_id=user.id,
            status='pending'
        ).first()
        already_sent = existing_request is not None

        # Privacy logic
        if profile.privacy_level == 0:
            can_view_full_profile = True
        elif profile.privacy_level == 1:
            can_view_full_profile = is_friend is not None
        elif profile.privacy_level == 2:
            can_view_full_profile = False

    # If profile is private (due to privacy rules), render private view
    if not can_view_full_profile:
        return render_template(
            'private_profile.html',
            username=user.username,
            profile_picture=profile.profile_pic,
            user=user,
            form=EmptyForm(),
            already_sent=already_sent  
        )

    # Mutual friends
    mutual_friends = list(set(current_user.friends) & set(user.friends))

    return render_template(
        'profile.html',
        user=user,
        profile=profile,
        mutual_friends=mutual_friends,
        can_view_full_profile=True,
        already_sent=already_sent,
        form=form
    )



@main.route('/search_users')
@login_required
def search_users():
    query = request.args.get('q', '')
    results = []
    if query:
        users = User.query.filter(User.username.ilike(f"%{query}%")).limit(10).all()
        results = [{"id": user.id, "username": user.username} for user in users if user.id != current_user.id]
    return jsonify(results)


@main.route('/reply/<int:post_id>', methods=['GET', 'POST'])
@login_required
def reply(post_id):
    parent_post = Post.query.get_or_404(post_id)
    form = PostForm()

    if form.validate_on_submit():
        reply = Post(content=form.content.data, user_id=current_user.id, parent=parent_post)
        db.session.add(reply)

        if parent_post.author.id != current_user.id:
            notif = Notification(
                user_id=parent_post.author.id,
                type='reply',
                content=f"{current_user.username} replied to your post",
                link=f"/post/{parent_post.id}"
            )
            db.session.add(notif)

        db.session.commit()
        flash('Reply posted!', 'success')
        return redirect(url_for('main.feed'))

    return render_template('reply.html', form=form, parent=parent_post)


@main.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    form = EmptyForm()

    if form.validate_on_submit():
        user = current_user  # Save reference before logout

        # Delete related FriendRequests
        FriendRequest.query.filter(
            (FriendRequest.sender_id == user.id) | (FriendRequest.receiver_id == user.id)
        ).delete()

        # Delete friendships
        Friend.query.filter(
            (Friend.user_id == user.id) | (Friend.friend_id == user.id)
        ).delete()

        # Delete profile
        if user.profile:
            db.session.delete(user.profile)

        # Delete user account
        db.session.delete(user)
        db.session.commit()
        logout_user()

        flash("Your account has been deleted.", "info")
        return redirect(url_for('main.login'))

    # Show confirmation page
    return render_template('confirm_delete.html', form=form)

@main.route('/debug_friend_requests')
def debug_friend_requests():
    requests = FriendRequest.query.all()
    return "<br>".join([f"{r.id}: {r.sender.username} ➝ {r.receiver.username} ({r.status})" for r in requests])


# @main.route('/messages/<int:user_id>')
# @login_required
# def message_user(user_id):
#     other_user = User.query.get_or_404(user_id)

#     # Get all messages between current user and the other user
#     messages = Message.query.filter(
#         ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
#         ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
#     ).order_by(Message.timestamp).all()

#     return render_template('messages.html', other_user=other_user, messages=messages)


@main.route('/messages')
@login_required
def messages():
    user_id = request.args.get('user_id', type=int)
    selected_user = User.query.get(user_id) if user_id else None

    # Step 1: Get all users the current user has chatted with
    messaged_user_ids = db.session.query(Message.sender_id).filter_by(receiver_id=current_user.id).union(
        db.session.query(Message.receiver_id).filter_by(sender_id=current_user.id)
    ).distinct().all()
    user_ids = [uid[0] for uid in messaged_user_ids if uid[0] != current_user.id]
    users = User.query.filter(User.id.in_(user_ids)).all()

    # Step 2: Load messages between current_user and selected_user
    chat_messages = []
    if selected_user:
        chat_messages = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == selected_user.id)) |
            ((Message.sender_id == selected_user.id) & (Message.receiver_id == current_user.id))
        ).order_by(Message.timestamp.asc()).all()

        # Mark messages from selected_user as read
        unread = Message.query.filter_by(sender_id=selected_user.id, receiver_id=current_user.id, read=False).all()
        for msg in unread:
            msg.read = True
        db.session.commit()

    # Step 3: Build recent conversations
    recent_conversations = []
    for user in users:
        last_msg = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == user.id)) |
            ((Message.sender_id == user.id) & (Message.receiver_id == current_user.id))
        ).order_by(Message.timestamp.desc()).first()

        if last_msg:
            unread_count = Message.query.filter_by(sender_id=user.id, receiver_id=current_user.id, read=False).count()
            recent_conversations.append({
                'user': user,
                'last_message': last_msg.content,
                'timestamp': last_msg.timestamp,
                'unread_count': unread_count
            })

    return render_template(
        'inbox.html',
        users=users,
        friends=current_user.friends,
        selected_user=selected_user,
        chat_messages=chat_messages,
        recent_conversations=sorted(recent_conversations, key=lambda x: x['timestamp'], reverse=True),
        my_id=current_user.id,
        other_user_id=user_id,
        other_username=selected_user.username if selected_user else '',
        my_avatar=current_user.profile.profile_pic if current_user.profile and current_user.profile.profile_pic else '/static/default-avatar.png',
        other_avatar=selected_user.profile.profile_pic if selected_user and selected_user.profile and selected_user.profile.profile_pic else '/static/default-avatar.png'
    )


@main.route("/notifications")
@login_required
def notifications():
    all_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
    return render_template("notifications.html", notifications=all_notifications)


@main.route('/api/unread_notifications')
@login_required
def unread_notifications():
    count = Notification.query.filter_by(user_id=current_user.id, read=False).count()
    return jsonify({'count': count})


@main.route("/notifications/mark_read/<int:notif_id>", methods=["POST"])
@login_required
def mark_notification_read(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        abort(403)
    notif.read = True
    db.session.commit()
    return jsonify({"status": "success", "notif_id": notif_id})



@main.route("/debug/messages")
def debug_messages():
    msgs = Message.query.all()
    return "<br>".join([f"{m.sender_id} -> {m.recipient_id}: {m.content}" for m in msgs])
