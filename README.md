# FlaskBlog

![Flask](https://img.shields.io/badge/Flask-2.3.2-blue)
![MongoDB](https://img.shields.io/badge/MongoDB-6.0-green)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple)

FlaskBlog is a fully functional blog application built with Flask, MongoDB, and Bootstrap. It allows users to create accounts, write blog posts, reset passwords, and interact with a modern and responsive user interface.

---

## Features

- **User Authentication**:
  - Register, login, and logout functionality.
  - Password reset via email.
  - User profile management (update username, email, and profile picture).

- **Blog Posts**:
  - Create, read, update, and delete blog posts.
  - Pagination for blog posts.
  - Sort posts by newest or oldest.

- **Responsive Design**:
  - Built with Bootstrap for a clean and modern UI.
  - Fully responsive for mobile and desktop devices.

- **Database**:
  - MongoDB for storing users, posts, and schemas.
  - Schema validation for posts and users.

- **Email Support**:
  - Send password reset emails using Flask-Mail.

---

## Installation

### Prerequisites

- Python 3.8+
- MongoDB (local or cloud instance)
- Flask dependencies

### Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/AmrMohamed27/flask-blog.git
   cd flask-blog
   ```
2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. **Install Dependencies**:
  ```bash
  pip install -r requirements.txt
  ```
4. **Set Up Environment Variables**:
  Create a .env file in the root directory and add the following variables:
  ```env
  SECRET_KEY=your_secret_key
  MONGO_URI=your_mongo_uri
  MAIL_SERVER=smtp.gmail.com
  MAIL_PORT=587
  MAIL_USE_TLS=True
  MAIL_USERNAME=your_email@gmail.com
  MAIL_PASSWORD=your_email_password
  ```
5. **Run the Application**:
   ```bash
   python run.py
   ```

6. **Access the Application**:
   Open your browser and navigate to http://127.0.0.1:5000.


### Project Structure
```bash
flask-blog/
├── flaskblog/
│   ├── __init__.py          # App factory and configuration
│   ├── config.py            # Configuration settings
│   ├── models.py            # User and Post models
│   ├── routes/
│   │   ├── main.py          # Main routes (home, about)
│   │   ├── users.py         # User authentication routes
│   │   ├── posts.py         # Blog post routes
│   ├── static/              # Static files (CSS, JS, images)
│   ├── templates/           # HTML templates
│   └── utils.py             # Helper functions
├── requirements.txt         # Project dependencies
├── run.py                   # Application entry point
└── README.md                # Project documentation
```
   
