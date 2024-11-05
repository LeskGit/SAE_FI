from ..app import app, db
from flask import render_template, url_for, redirect, request
#from .models import 
from flask_wtf import FlaskForm
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256

@app.route("/connexion")
def connexion() :
    return render_template("connexion.html")

@app.route("/inscription")
def inscription() :
    return render_template("inscription.html")