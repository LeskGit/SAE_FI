from project import app, db
from flask import render_template, url_for, redirect, request
from models import User
from flask_wtf import FlaskForm, RecaptchaField
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from wtforms import StringField, PasswordField, EmailField

class LoginForm (FlaskForm):
    phone_number = StringField("Numero_telephone")
    password = PasswordField("Mot_de_passe")

class RegisterForm (FlaskForm):
    phone_number = StringField("Numero_telephone")
    name = StringField("Nom")
    first_name = StringField("Prenom")
    password = PasswordField("Mot_de_passe")
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
        user = f.get_authenticated_user()
        if user:
            login_user(user)
            return render_template("profil_client_connecte.html", client = user) 
    return render_template("connexion.html", form = f)

@app.route("/deconnexion")
def logout():
    logout_user()
    return redirect(url_for("accueil"))

@app.route("/inscription")
def register():
    f = RegisterForm()
    if f.validate_on_submit():
        phone = f.phone_number.data
        passwd = f.password.data
        name = f.name.data
        first_name = f.first_name.data
        addresse = f.addresse.data
        mail = f.email.data
        m = sha256()
        m.update(passwd.encode())
        u = User(num_tel=phone, password=m.hexdigest(), nom = name, prenom = first_name, adresse = addresse, email = mail)
        db.session.add(u)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("inscription.html", form = f)