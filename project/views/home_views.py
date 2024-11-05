from wtforms import EmailField, StringField, TextAreaField
from project import app, db
from flask import render_template, url_for, redirect, request
#from .models import 
from flask_wtf import FlaskForm
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256

class ContactForm(FlaskForm):
    email = EmailField('Email')
    objet = StringField('Objet')
    message = TextAreaField('Message')

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/a_propos")
def a_propos():
    return render_template("a_propos.html")

@app.route("/nouveaute")
def nouveaute():
    return render_template("nouveaute.html")

@app.route("/contact")
def contact():
    f = ContactForm()
    return render_template("contact.html", form=f)