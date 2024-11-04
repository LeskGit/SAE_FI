from project import app, db
from flask import render_template, url_for, redirect, request
from models import User
from flask_wtf import FlaskForm, RecaptchaField
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from wtforms import StringField, PasswordField, EmailField

class LoginForm (FlaskForm) :
    num_tel = StringField("Numero_telephone")
    password = PasswordField("Mot_de_passe")

class RegisterForm ( FlaskForm ) :
    num_tel = StringField("Numero_telephone")
    nom = StringField("Nom")
    prenom = StringField("Prenom")
    password = PasswordField("Mot_de_passe")
    adresse = StringField("Adresse")
    email = EmailField("Email")
    repcatcha = RecaptchaField()

    def get_user_authentifie(self):
        """permet de savoir si le mot de passe de 
        l'utilisateur est bon

        Returns:
            User: L'utilisateur si le mot de passe est correct, None sinon
        """
        user = User.query.get(self.num_tel.data)
        if user is None:
            return None
        m = sha256 ()
        m.update(self.password.data.encode())
        passwd = m.hexdigest ()
        return user if passwd == user.password else None

@app.route("/connexion", methods = ("GET", "POST", ))
def connexion() :
    f = LoginForm()
    if f.validate_on_submit ():
        user = f.get_authenticated_user ()
        if user :
            login_user(user)
            return render_template("profil_client_connecte.html", client = user) 
    return render_template("connexion.html", form = f)

@app.route("/deconnexion")
def logout ():
    logout_user ()
    return redirect ( url_for ("accueil"))

@app.route("/inscription")
def inscription() :
    f = RegisterForm()
    if f.validate_on_submit():
        numero_tel = f.num_tel.data
        password = f.password.data
        nom_c = f.nom.data
        prenom_c = f.prenom.data
        adresse_c = f.adresse.data
        email_c = f.email.data
        m = sha256()
        m.update(password.encode())
        u = User(num_tel=numero_tel, password=m.hexdigest(), nom = nom_c, prenom = prenom_c, adresse = adresse_c, email = email_c)
        db.session.add(u)
        db.session.commit()
        return redirect(url_for("connexion"))
    return render_template("inscription.html", form = f)