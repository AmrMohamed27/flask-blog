# Register page
from flask import Blueprint, render_template, url_for, flash, redirect, request, jsonify, current_app
from flaskblog.users.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                             RequestResetForm, ResetPasswordForm)
from datetime import datetime
from bson.objectid import ObjectId
from flaskblog import bcrypt, User
from flask_login import login_user, current_user, logout_user, login_required
from flaskblog.utils import save_image, send_email
from flaskblog import mongo


users_blueprint = Blueprint("users", __name__)

@users_blueprint.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = {"username": form.username.data, "email": form.email.data, "password": hashed_password, "date_joined": datetime.now(), "image": "default.jpg"}
        user_id = mongo.db.users.insert_one(user).inserted_id
        flash(f'Account created for {user["username"]}! You can now log in', category="success")
        return redirect(url_for("users.login"))
    return render_template("register.html",title="Register" , form=form)

# Login page
@users_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:  # Redirect if already logged in
        return redirect(url_for("main.home"))
    form = LoginForm()
    if form.validate_on_submit():
         user_data = mongo.db.users.find_one({"email": form.email.data})
         if user_data and bcrypt.check_password_hash(user_data["password"], form.password.data):
            user = User(str(user_data["_id"]), user_data["username"], user_data["email"], user_data["image"])
            login_user(user, remember=form.remember.data)
            flash('You have been logged in!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for("main.home"))
         else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template("login.html",title="Login" , form=form)

# Logout Page
@users_blueprint.route("/logout")
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for("main.home"))





# Account Page
@users_blueprint.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        new_image = save_image(form.image.data)
        mongo.db.users.update_one({"_id": ObjectId(current_user.id)}, {"$set": {"username": form.username.data, "email": form.email.data, "image": new_image}})
        updated_user_data = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
        current_user.username = updated_user_data["username"]
        current_user.email = updated_user_data["email"]
        current_user.image = updated_user_data["image"]
        flash(f'Account updated successfully!', category="success")
        return redirect(url_for("users.account"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for("static", filename="profile_pics/" + current_user.image)
    return render_template("account.html", title="Account", image_file=image_file, form=form)


### Users

# Add a new user
@users_blueprint.route('/api/users/add', methods=['POST'])
def add_user():
    data = request.form
    # Create a new user object excluding 'confirm_password'
    user = {"username": data["username"], "email": data["email"], "password": data["password"], "date_joined": datetime.now()}
    mongo.db.users.insert_one(user)
    flash(f'{user["email"]} signed in!', category="success")
    return redirect(url_for("main.home"))

# Get all users
@users_blueprint.route('/api/users', methods=['GET'])
def get_all_users():
    users = list(mongo.db.users.find({}, {"_id": 0}))
    return jsonify(users)

# Update a user
@users_blueprint.route('/api/users/update', methods=['PUT'])
def update_user():
    data = request.json
    mongo.db.users.update_one({"_id": data["_id"]}, {"$set": data})
    return jsonify({"message": "User updated successfully!"})

# Delete a user
@users_blueprint.route('/api/users/delete', methods=['DELETE'])
def delete_user():
    data = request.json
    mongo.db.users.delete_one({"username": data["username"]})
    return jsonify({"message": "User deleted successfully!"})

# Get user posts
@users_blueprint.route('/api/users/<user_id>/posts', methods=['GET'])
def get_user_posts(user_id):
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Fetch posts using the `posts` field
    posts = list(mongo.db.posts.find({"_id": {"$in": user["posts"]}}))
    return jsonify(posts)




# Request password reset
@users_blueprint.route('/reset_password', methods=['GET', 'POST'])
def request_reset():
    if current_user.is_authenticated:  # Redirect if already logged in
        return redirect(url_for("main.home"))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = mongo.db.users.find_one({"email": form.email.data})
        if user:
            user_instance = User(str(user["_id"]), user["username"], user["email"], user["image"])
            token = user_instance.get_reset_token()
            send_email(user["email"], "Reset Password", token)
            flash(f"Password reset email sent to {user["email"]}!", category="info")
            return redirect(url_for("main.home"))
        else:
            flash("No account found with that email!", category="danger")
            return redirect(url_for("main.    home"))
    return render_template("request_reset.html", form=form, title="Reset Password")

# password reset
@users_blueprint.route('/reset_password/<token>', methods=['GET', 'POST'])
def request_token(token):
    if current_user.is_authenticated:  # Redirect if already logged in
        return redirect(url_for("main.home"))
    user = User.verify_reset_token(token)
    if user is None:
        flash("Invalid token!", category="danger")
        return redirect(url_for("main.home"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        data = {"password": hashed_password}
        res = mongo.db.users.update_one({"_id": ObjectId(user.id)}, {"$set": data })
        print(res.modified_count)
        flash(f'Your password has been updated! You can now log in', category="success")
        return redirect(url_for("users.login"))
    return render_template("reset_password.html", form=form, title="Reset Password", token=token)