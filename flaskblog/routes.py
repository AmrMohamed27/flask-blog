from flask import render_template, url_for, flash, redirect, request, jsonify
from flaskblog.forms import (RegistrationForm, LoginForm, UpdateAccountForm, AddPostForm,
                             UpdatePostForm, RequestResetForm, ResetPasswordForm)
from PIL import Image
from datetime import datetime
from bson.objectid import ObjectId
from flaskblog import app, db, bcrypt, User, mail
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
from flask_mail import Message


# Homepage
@app.route("/")
def home():
    # Get page number from URL parameters, default to 1
    page = request.args.get('page', 1, type=int)
    sort = request.args.get("sort", "newest", type=str)
    sortBy = {"date_posted": -1} if sort == "newest" else {"date_posted": 1}
    posts_per_page = 4
    skip = (page - 1) * posts_per_page
    total_posts = db.posts.count_documents({})
    total_pages = (total_posts + posts_per_page - 1) // posts_per_page

    posts = list(db.posts.aggregate([
        {
            "$lookup": {
                "from": "users",
                "localField": "author",
                "foreignField": "_id",
                "as": "author_details"
            }
        },
        {"$unwind": "$author_details"},
        {
            "$project": {
                "_id": 1,
                "title": 1,
                "content": 1,
                "date_posted": 1,
                "author_details.username": 1
            }
        },
        {"$sort": sortBy},  # Sort by date, newest first
        {"$skip": skip},
        {"$limit": posts_per_page}
    ]))

    return render_template(
        "home.html",
        posts=posts,
        page=page,
        total_pages=total_pages,
        has_prev=page > 1,
        has_next=page < total_pages,
        sort=sort
    )

# About page
@app.route("/about")
def about():
    return render_template("about.html", title="About")

# Register page
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = {"username": form.username.data, "email": form.email.data, "password": hashed_password, "date_joined": datetime.now(), "image": "default.jpg"}
        user_id = db.users.insert_one(user).inserted_id
        flash(f'Account created for {user["username"]}! You can now log in', category="success")
        return redirect(url_for("login"))
    return render_template("register.html",title="Register" , form=form)

# Login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:  # Redirect if already logged in
        return redirect(url_for("home"))
    form = LoginForm()
    if form.validate_on_submit():
         user_data = db.users.find_one({"email": form.email.data})
         if user_data and bcrypt.check_password_hash(user_data["password"], form.password.data):
            user = User(str(user_data["_id"]), user_data["username"], user_data["email"], user_data["image"])
            login_user(user, remember=form.remember.data)
            flash('You have been logged in!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for("home"))
         else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template("login.html",title="Login" , form=form)

# Logout Page
@app.route("/logout")
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for("home"))


# Function to upload image
def save_image(form_image):
    if form_image:
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_image.filename)
        image_fn = random_hex + f_ext
        image_path = os.path.join(app.root_path, "static/profile_pics", image_fn)
        output_size = (125, 125)
        i = Image.open(form_image)
        i.thumbnail(output_size)
        i.save(image_path)
        return image_fn
    else:
        return current_user.image


# Account Page
@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        new_image = save_image(form.image.data)
        db.users.update_one({"_id": ObjectId(current_user.id)}, {"$set": {"username": form.username.data, "email": form.email.data, "image": new_image}})
        updated_user_data = db.users.find_one({"_id": ObjectId(current_user.id)})
        current_user.username = updated_user_data["username"]
        current_user.email = updated_user_data["email"]
        current_user.image = updated_user_data["image"]
        flash(f'Account updated successfully!', category="success")
        return redirect(url_for("account"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for("static", filename="profile_pics/" + current_user.image)
    return render_template("account.html", title="Account", image_file=image_file, form=form)


### Posts

# Add a new post
@app.route('/posts/add', methods=['GET', 'POST'])
def add_post():
    form = AddPostForm()
    if form.validate_on_submit():
        data = request.form
        user_id = ObjectId(current_user.id)  # Ensure author is a valid ObjectId
        post = {"author": user_id, "title": data["title"], "content": data["content"], "date_posted": datetime.now()}
        # Add the new post
        post_id = db.posts.insert_one(post).inserted_id
        # Update the user's posts array
        db.users.update_one(
            {"_id": user_id},
            {"$push": {"posts": post_id}}
        )
        flash(f"Post added successfully!", category="success")
        return redirect(url_for("home"))
    elif request.method == "GET":
        form.title.data = ""
        form.content.data = ""
        return render_template("add_post.html", title="Create Post", form=form, endpoint=url_for("add_post"))
    

# Get a post by id
# Route for individual post
@app.route("/post/<post_id>")
def post(post_id):
    # Fetch the post by its ID and join with the users collection to get author details
    post = list(db.posts.aggregate([
        {
            "$match": {"_id": ObjectId(post_id)}  # Match the post by its ID
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "author",
                "foreignField": "_id",
                "as": "author_details"
            }
        },
        {"$unwind": "$author_details"},  # Flatten the author details array
        {
            "$project": {
                "_id": 1,
                "title": 1,
                "content": 1,
                "date_posted": 1,
                "author_details.username": 1
            }
        }
    ]))

    if not post:
        flash("Post not found!", category="danger")
        return redirect(url_for("home"))

    # Since aggregation returns a list, take the first (and only) result
    post = post[0]
    return render_template("post.html", post=post)

# Get all posts
@app.route('/api/posts', methods=['GET'])
def get_all_posts():
    posts = list(db.posts.aggregate([
        {
            "$lookup": {
                "from": "users",
                "localField": "author",
                "foreignField": "_id",
                "as": "author_details"
            }
        },
        {"$unwind": "$author_details"},  # Flatten the author details array
        {
            "$project": {
                "_id": 0,
                "title": 1,
                "content": 1,
                "date_posted": 1,
                "author_details.username": 1,
                "author_details.email": 1
            }
        }
    ]))
    return jsonify(posts)

# Update a post
@app.route("/post/<post_id>/update", methods=["GET", "POST"])
@login_required
def update_post(post_id):
    form = UpdatePostForm()
    # Fetch the post
    post = db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        flash("Post not found!", category="danger")
        return redirect(url_for("home"))

    # Check if the current user is the author of the post
    if post["author"] != ObjectId(current_user.id):
        flash("You are not authorized to update this post!", category="danger")
        return redirect(url_for("home"))

    if request.method == "POST":
        # Update the post
        title = request.form.get("title")
        content = request.form.get("content")
        db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {"title": title, "content": content}}
        )
        flash("Post updated successfully!", category="success")
        return redirect(url_for("post", post_id=post_id))

    # Render the update form with the current post data
    else:
        form.title.data = post["title"]
        form.content.data = post["content"]
        return render_template("add_post.html", post=post, form=form, title="Update Post", endpoint=url_for("update_post", post_id=post_id))

# Delete the post
@app.route("/post/<post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    try:
        # Fetch the post
        post = db.posts.find_one({"_id": ObjectId(post_id)})
        if not post:
            flash("Post not found!", category="danger")
            return redirect(url_for("home"))

        # Check if the current user is the author of the post
        if post["author"] != ObjectId(current_user.id):
            flash("You are not authorized to delete this post!", category="danger")
            return redirect(url_for("home"))

        # Delete the post
        db.posts.delete_one({"_id": ObjectId(post_id)})
        
        # Remove the post reference from the user's posts array
        db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$pull": {"posts": ObjectId(post_id)}}
        )
        
        flash("Post deleted successfully!", category="success")
        return redirect(url_for("home"))
        
    except Exception as e:
        flash(f"An error occurred while deleting the post: {str(e)}", category="danger")
        return redirect(url_for("home"))


### Users

# Add a new user
@app.route('/api/users/add', methods=['POST'])
def add_user():
    data = request.form
    # Create a new user object excluding 'confirm_password'
    user = {"username": data["username"], "email": data["email"], "password": data["password"], "date_joined": datetime.now()}
    db.users.insert_one(user)
    flash(f'{user["email"]} signed in!', category="success")
    return redirect(url_for("home"))

# Get all users
@app.route('/api/users', methods=['GET'])
def get_all_users():
    users = list(db.users.find({}, {"_id": 0}))
    return jsonify(users)

# Update a user
@app.route('/api/users/update', methods=['PUT'])
def update_user():
    data = request.json
    db.users.update_one({"_id": data["_id"]}, {"$set": data})
    return jsonify({"message": "User updated successfully!"})

# Delete a user
@app.route('/api/users/delete', methods=['DELETE'])
def delete_user():
    data = request.json
    db.users.delete_one({"username": data["username"]})
    return jsonify({"message": "User deleted successfully!"})

# Get user posts
@app.route('/api/users/<user_id>/posts', methods=['GET'])
def get_user_posts(user_id):
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Fetch posts using the `posts` field
    posts = list(db.posts.find({"_id": {"$in": user["posts"]}}))
    return jsonify(posts)




# Request password reset
@app.route('/reset_password', methods=['GET', 'POST'])
def request_reset():
    if current_user.is_authenticated:  # Redirect if already logged in
        return redirect(url_for("home"))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = db.users.find_one({"email": form.email.data})
        if user:
            user_instance = User(str(user["_id"]), user["username"], user["email"], user["image"])
            token = user_instance.get_reset_token()
            send_email(user["email"], "Reset Password", token)
            flash(f"Password reset email sent to {user["email"]}!", category="info")
            return redirect(url_for("home"))
        else:
            flash("No account found with that email!", category="danger")
            return redirect(url_for("home"))
    return render_template("request_reset.html", form=form, title="Reset Password")


# Send Email
def send_email(to, subject, token):
    msg = Message(subject, sender=app.config["MAIL_USERNAME"], recipients=[to])
    msg.body = f'''To reset your password, please click the following link:
{url_for('request_token', token=token, _external=True)}

If you did not request a password reset, please ignore this email.
    '''
    mail.send(msg)

# password reset
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def request_token(token):
    if current_user.is_authenticated:  # Redirect if already logged in
        return redirect(url_for("home"))
    user = User.verify_reset_token(token)
    if user is None:
        flash("Invalid token!", category="danger")
        return redirect(url_for("home"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        data = {"password": hashed_password}
        res = db.users.update_one({"_id": ObjectId(user.id)}, {"$set": data })
        print(res.modified_count)
        flash(f'Your password has been updated! You can now log in', category="success")
        return redirect(url_for("login"))
    return render_template("reset_password.html", form=form, title="Reset Password", token=token)