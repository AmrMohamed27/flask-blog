from flask import Flask, current_app
from dotenv import load_dotenv
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin
from bson.objectid import ObjectId
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from flask_mail import Mail

# Load .env variables
load_dotenv()

# Initialize extensions (without app context)
mail = Mail()
mongo = PyMongo()
bcrypt = Bcrypt()
login_manager = LoginManager()

# Define schemas
post_schema = {
    "bsonType": "object",
    "required": ["author", "title", "content", "date_posted"],
    "properties": {
        "author": {
            "bsonType": "objectId",
            "description": "Author must be a valid ObjectId referencing the users collection"
        },
        "title": {"bsonType": "string", "description": "Title must be a string"},
        "content": {"bsonType": "string", "description": "Content must be a string"},
        "date_posted": {"bsonType": "date", "description": "Date must be a valid date"},
    },
}

user_schema = {
    "bsonType": "object",
    "required": ["username", "email", "password"],
    "properties": {
        "username": {"bsonType": "string", "description": "Username must be a string"},
        "email": {"bsonType": "string", "description": "Email must be a string"},
        "password": {"bsonType": "string", "description": "Password must be a string"},
        "date_joined": {"bsonType": "date", "description": "Date must be a valid date"},
        "image": {"bsonType": "string", "description": "Image must be a string"},
        "posts": {
            "bsonType": "array",
            "items": {"bsonType": "objectId"},
            "description": "List of post ObjectIds authored by the user"
        }
    },
}

# User class
class User(UserMixin):
    def __init__(self, id, username, email, image):
        self.id = id
        self.username = username
        self.email = email
        self.image = image

    @staticmethod
    def get(user_id):
        user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not user_data:
            return None
        return User(str(user_data["_id"]), user_data["username"], user_data["email"], user_data["image"])
    
    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config["SECRET_KEY"])
        return s.dumps({"id": self.id})
    
    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except:
            return None
        return User.get(data["id"])

# Login manager setup
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

login_manager.login_view = "users.login"
login_manager.login_message_category = 'info'

# App factory function
def create_app(config_class="flaskblog.config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app
    mongo.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Apply schema validation after initializing the app and database
    with app.app_context():
        db = mongo.db
        if db is not None:
            db.command("collMod", "posts", validator={"$jsonSchema": post_schema})
            db.command("collMod", "users", validator={"$jsonSchema": user_schema})

    # Register blueprints
    from flaskblog.users.routes import users_blueprint
    from flaskblog.posts.routes import posts_blueprint
    from flaskblog.main.routes import main_blueprint
    app.register_blueprint(users_blueprint)
    app.register_blueprint(posts_blueprint)
    app.register_blueprint(main_blueprint)

    return app