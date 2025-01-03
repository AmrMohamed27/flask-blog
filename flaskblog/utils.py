# Send Email
from flask import url_for
from flaskblog import app, mail
from flask_mail import Message
from flask_login import current_user
from PIL import Image
import secrets
import os

def send_email(to, subject, token):
    msg = Message(subject, sender=app.config["MAIL_USERNAME"], recipients=[to])
    msg.body = f'''To reset your password, please click the following link:
{url_for('users.request_token', token=token, _external=True)}

If you did not request a password reset, please ignore this email.
    '''
    mail.send(msg)


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