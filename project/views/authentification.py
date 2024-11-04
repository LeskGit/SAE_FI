from project import app, db
from flask import render_template, url_for, redirect, request
from models import User
from flask_wtf import FlaskForm, RecaptchaField
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from wtforms import StringField, PasswordField, EmailField

class LoginForm ( FlaskForm ) :
    num_tel = StringField("Numero_telephone")
    nom = StringField("Nom")
    prenom = StringField("Prenom")
    mot_de_passe = PasswordField("Mot_de_passe")
    adresse = StringField("Adresse")
    email = EmailField("Email")
    repcatcha = RecaptchaField()

    def get_user_authentifie(self):
        user = User.query.get(self.num_tel.data)
        if user is None:
            return None
        m = sha256 ()
        m.update(self.password.data.encode())
        passwd = m.hexdigest ()
        return user if passwd == user.password else None

@app.route("/connexion")
def connexion() :
    return render_template("connexion.html")

@app.route("/inscription")
def inscription() :
    return render_template("inscription.html")