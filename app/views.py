from .app import app
from flask import render_template
from .app import db


@app.route ("/")
def home():
    return render_template(
        "base.html")
