from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flaskblog import db
from flask_login import current_user

class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(), Length(min=2, max=20)
        ])
    email = StringField("Email", validators=[DataRequired(), Email(message="Invalid email")])
    password = PasswordField("Password", validators=[
        DataRequired(), Length(min=6, max=20)
        ])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(), Length(min=6, max=20), EqualTo("password", message="Passwords don't match")
        ])
    submit = SubmitField("Sign Up")
    
    def validate_username(self, username):
        user = db.users.find_one({"username": username.data})
        if user:
            raise ValidationError("Username already exists")
        
    def validate_email(self, email):
        user = db.users.find_one({"email": email.data})
        if user:
            raise ValidationError("Email already exists")
    
    
    
    
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(message="Invalid email")])
    password = PasswordField("Password", validators=[
        DataRequired(), Length(min=6, max=20)
        ])
    remember = BooleanField("Remember Me?")
    submit = SubmitField("Login")
    

class UpdateAccountForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(), Length(min=2, max=20)
        ])
    email = StringField("Email", validators=[DataRequired(), Email(message="Invalid email")])
    image = FileField("Upload new Image", validators=[FileAllowed(["jpg", "png", "jpeg"], "Please upload a valid image.")])
    submit = SubmitField("Update")
    
    def validate_username(self, username):
        if username.data != current_user.username:
            user = db.users.find_one({"username": username.data})
            if user:
                raise ValidationError("Username already exists")

    def validate_email(self, email):
        if email.data != current_user.email:
            user = db.users.find_one({"email": email.data})
            if user:
                raise ValidationError("Email already exists")


    
class RequestResetForm(FlaskForm):
     email = StringField("Email", validators=[DataRequired(), Email(message="Invalid email")])
     submit = SubmitField("Request Password Reset")
     
     def validate_email(self, email):
        user = db.users.find_one({"email": email.data})
        if user is None:
            raise ValidationError("There is no account with that email. Please create an account first.")
        
class ResetPasswordForm(FlaskForm):
    password = PasswordField("Password", validators=[
    DataRequired(), Length(min=6, max=20)
    ])
    confirm_password = PasswordField("Confirm Password", validators=[
    DataRequired(), Length(min=6, max=20), EqualTo("password", message="Passwords don't match")
    ])
    submit = SubmitField("Reset Password")