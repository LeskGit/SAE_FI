from . import app
from flask import render_template, url_for, redirect, request

@app.route("/")
def home():
    images = ["img/slide-1.jpg", "img/slide-2.jpg", "img/slide-3.jpg"]
    return render_template("home.html",
                           images=images)