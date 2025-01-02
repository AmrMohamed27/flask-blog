from flask import Flask
from dotenv import load_dotenv
import os
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin
from bson.objectid import ObjectId
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from flask_mail import Mail



# Load .env variables
load_dotenv()
# Initialize Flask and Get Environment Variables
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT"))
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
mail = Mail(app)

# Initialize PyMongo
mongo = PyMongo(app)
# Access the database
db = mongo.db

# Define a schema for the 'posts' collection
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
# Define a schema for the 'users' collection
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
# Apply the schema validation
db.command("collMod", "posts", validator={"$jsonSchema": post_schema})
db.command("collMod", "users", validator={"$jsonSchema": user_schema})

# Bcrypt
bcrypt = Bcrypt(app)

# Login Manager
login_manager = LoginManager(app)


# Redirect to login page if user is not logged in
login_manager.login_view = "login"
login_manager.login_message_category = 'info'  # Flash message category for login required

class User(UserMixin):
    def __init__(self, id, username, email, image):
        self.id = id
        self.username = username
        self.email = email
        self.image = image

    @staticmethod
    def get(user_id):
        user_data = db.users.find_one({"_id": ObjectId(user_id)})
        if not user_data:
            return None
        return User(str(user_data["_id"]), user_data["username"], user_data["email"], user_data["image"])
    
    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config["SECRET_KEY"])
        return s.dumps({"id": self.id})
    
    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except:
            return None
        return User.get(data["id"])


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)



from flaskblog import routes