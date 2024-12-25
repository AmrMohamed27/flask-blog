from flask import Flask, render_template, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = "nrVnX+mde9bZyCd8eGlXtN6nhd1/m8wprMZSNSppNF0="

posts = [
    {
        "author": "Amr Mohamed",
        "title": "How to make a blog with Flask",
        "content": "First Post Content",
        "date_posted": "December 24th, 2024",
    },
    {
        "author": "John Doe",
        "title": "How to make a blog with Flask",
        "content": "Second Post Content",
        "date_posted": "December 23th, 2024",
    }
]

@app.route("/")
def root():
    return render_template("home.html", posts=posts)

@app.route("/about")
def about():
    return render_template("about.html", title="About")

if __name__ == "__main__":
    app.run(debug=True)