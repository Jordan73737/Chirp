from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.forms import RegisterForm, LoginForm, LikeForm
from app import db, login_manager
from flask_login import login_user, logout_user, login_required, current_user
from app.forms import PostForm
from app.models import User, Post, Like


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
    return render_template('profile.html', user=current_user)

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

