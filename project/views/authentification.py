from project import app, db
from flask import render_template, url_for, redirect, request
from flask_wtf import FlaskForm, RecaptchaField
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from wtforms import StringField, PasswordField, EmailField
from project.models import User

class LoginForm (FlaskForm):
    phone_number = StringField("Numéro de téléphone")
    password = PasswordField("Mot de passe")

class RegisterForm (FlaskForm):
    phone_number = StringField("Numéro téléphone")
    name = StringField("Nom")
    first_name = StringField("Prénom")
    password = PasswordField("Mot de passe")
    addresse = StringField("Adresse")
    email = EmailField("Email")
    repcatcha = RecaptchaField()

    def get_authentificated_user(self):
        """permet de savoir si le mot de passe de 
        l'utilisateur est bon

        Returns:
            User: L'utilisateur si le mot de passe est correct, None sinon
        """
        user = User.query.get(self.num_tel.data)
        if user is None:
            return None
        m = sha256()
        m.update(self.password.data.encode())
        passwd = m.hexdigest()
        return user if passwd == user.password else None

@app.route("/connexion", methods = ("GET", "POST", ))
def login():
    f = LoginForm()
    if f.validate_on_submit():
        the_user = f.get_authenticated_user()
        if the_user:
            login_user(the_user)
            return render_template("profil_client_connecte.html", user = the_user) 
    return render_template("connexion.html", form = f)

@app.route("/deconnexion")
def logout():
    logout_user()
    return redirect(url_for("accueil"))

@app.route("/inscription")
def register():
    f = RegisterForm()
    if f.validate_on_submit():
        passwd = f.password.data
        m = sha256()
        m.update(passwd.encode())
        u = User(num_tel=f.phone_number.data, password=m.hexdigest(), 
                 nom = f.name.data, 
                 prenom = f.first_name.data, 
                 adresse = f.addresse.data, 
                 email = f.email.data)
        db.session.add(u)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("inscription.html", form = f)