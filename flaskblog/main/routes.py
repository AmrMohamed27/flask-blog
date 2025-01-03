from flask import render_template, request, Blueprint
from flaskblog import app, db

main_blueprint = Blueprint("main", __name__)

# Homepage
@main_blueprint.route("/")
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
@main_blueprint.route("/about")
def about():
    return render_template("about.html", title="About")