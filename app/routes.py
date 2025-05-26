from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app.forms import RegisterForm, LoginForm, LikeForm, ProfileForm, PostForm, EmptyForm
from app import db, login_manager
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Post, Like, Profile, Friend, FriendRequest

# main is the type of route that we will use, which is of type BluePrint (in-built flask Blueprint)
main = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/settings')
@login_required
def settings():
    return render_template('settings.html', user=current_user)


@main.route('/profile')
@login_required
def profile():
    form = EmptyForm()  # CSRF protection
    mutual_friends = set(current_user.friends).intersection(current_user.friend_of)
    return render_template('profile.html', user=current_user, form=form, mutual_friends=mutual_friends)


@main.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user.profile)

    if form.validate_on_submit():
        if not current_user.profile:
            current_user.profile = Profile(user=current_user)

        current_user.profile.bio = form.bio.data
        current_user.profile.location = form.location.data
        current_user.profile.website = form.website.data
        current_user.profile.profile_pic = form.profile_pic.data

        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('main.profile'))

    return render_template('edit_profile.html', form=form)

@main.route('/user/<int:user_id>')
@login_required
def view_user_profile(user_id):
    user = User.query.get_or_404(user_id)
    form = EmptyForm()

    mutual_friends = set(user.friends).intersection(current_user.friends)

    return render_template('profile.html', user=user, form=form, mutual_friends=mutual_friends)


@main.route('/friend_request/send/<int:user_id>', methods=['POST'])
@login_required
def send_friend_request(user_id):
    if user_id == current_user.id:
        flash("You can't send a friend request to yourself.", "warning")
        return redirect(url_for('main.profile'))

    existing_request = FriendRequest.query.filter_by(sender_id=current_user.id, receiver_id=user_id).first()
    if existing_request:
        flash("Friend request already sent.", "info")
    else:
        new_request = FriendRequest(sender_id=current_user.id, receiver_id=user_id)
        db.session.add(new_request)
        db.session.commit()
        flash("Friend request sent!", "success")

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

    posts = Post.query.order_by(Post.timestamp.desc()).all()
    liked_post_ids = {like.post_id for like in current_user.likes}

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


@main.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        flash("You can't delete this post.", 'danger')
        return redirect(url_for('main.feed'))

    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'info')
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

    if user.id == current_user.id:
        return redirect(url_for('main.profile'))

    mutual_friends = list(set(current_user.friends) & set(user.friends))

    return render_template('profile.html', user=user, mutual_friends=mutual_friends)


@main.route('/search_users')
@login_required
def search_users():
    query = request.args.get('q', '')
    results = []
    if query:
        users = User.query.filter(User.username.ilike(f"%{query}%")).limit(10).all()
        results = [{"id": user.id, "username": user.username} for user in users if user.id != current_user.id]
    return jsonify(results)
