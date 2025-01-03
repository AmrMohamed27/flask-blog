from flask import Blueprint, render_template, url_for, flash, redirect, request, jsonify
from flaskblog.posts.forms import ( AddPostForm, UpdatePostForm)
from datetime import datetime
from bson.objectid import ObjectId
from flaskblog import db
from flask_login import  current_user, login_required

posts_blueprint = Blueprint("posts", __name__)


### Posts

# Add a new post
@posts_blueprint.route('/posts/add', methods=['GET', 'POST'])
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
        return redirect(url_for("main.home"))
    elif request.method == "GET":
        form.title.data = ""
        form.content.data = ""
        return render_template("add_post.html", title="Create Post", form=form, endpoint=url_for("posts.add_post"))
    

# Get a post by id
# Route for individual post
@posts_blueprint.route("/post/<post_id>")
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
        return redirect(url_for("main.home"))

    # Since aggregation returns a list, take the first (and only) result
    post = post[0]
    return render_template("post.html", post=post)

# Get all posts
@posts_blueprint.route('/api/posts', methods=['GET'])
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
@posts_blueprint.route("/post/<post_id>/update", methods=["GET", "POST"])
@login_required
def update_post(post_id):
    form = UpdatePostForm()
    # Fetch the post
    post = db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        flash("Post not found!", category="danger")
        return redirect(url_for("main.home"))

    # Check if the current user is the author of the post
    if post["author"] != ObjectId(current_user.id):
        flash("You are not authorized to update this post!", category="danger")
        return redirect(url_for("main.home"))

    if request.method == "POST":
        # Update the post
        title = request.form.get("title")
        content = request.form.get("content")
        db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {"title": title, "content": content}}
        )
        flash("Post updated successfully!", category="success")
        return redirect(url_for("posts.post", post_id=post_id))

    # Render the update form with the current post data
    else:
        form.title.data = post["title"]
        form.content.data = post["content"]
        return render_template("add_post.html", post=post, form=form, title="Update Post", endpoint=url_for("posts.update_post", post_id=post_id))

# Delete the post
@posts_blueprint.route("/post/<post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    try:
        # Fetch the post
        post = db.posts.find_one({"_id": ObjectId(post_id)})
        if not post:
            flash("Post not found!", category="danger")
            return redirect(url_for("main.home"))

        # Check if the current user is the author of the post
        if post["author"] != ObjectId(current_user.id):
            flash("You are not authorized to delete this post!", category="danger")
            return redirect(url_for("main.home"))

        # Delete the post
        db.posts.delete_one({"_id": ObjectId(post_id)})
        
        # Remove the post reference from the user's posts array
        db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$pull": {"posts": ObjectId(post_id)}}
        )
        
        flash("Post deleted successfully!", category="success")
        return redirect(url_for("main.home"))
        
    except Exception as e:
        flash(f"An error occurred while deleting the post: {str(e)}", category="danger")
        return redirect(url_for("main.home"))