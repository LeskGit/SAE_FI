from project import app, db
from flask import render_template, url_for, redirect, request
from flask_wtf import FlaskForm, RecaptchaField
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from wtforms import StringField, PasswordField, EmailField
from wtforms.validators import DataRequired, EqualTo, Email, Length, Regexp
from email_validator import EmailNotValidError
from project.models import User

class LoginForm (FlaskForm):
    phone_number = StringField("Numéro de téléphone", validators=[DataRequired(), 
                                                                  Length(min=10, max=10, message = 'Longueur incorrect'), 
                                                                  Regexp(r'^\d{10}$', message="Le numéro de téléphone doit contenir uniquement des chiffres.")])
    password = PasswordField("Mot de passe", validators=[DataRequired(), Length(max=64)])

    def get_authentificated_user(self):
        """permet de savoir si le mot de passe de 
        l'utilisateur est bon

        Returns:
            User: L'utilisateur si le mot de passe est correct, None sinon
        """
        user = User.query.get(self.phone_number.data)
        if user is None:
            return None
        m = sha256()
        m.update(self.password.data.encode())
        passwd = m.hexdigest()
        return user if passwd == user.mdp else None

class RegisterForm (FlaskForm):
    phone_number = StringField("Numéro téléphone", validators=[DataRequired(), 
                                                               Length(min=10, max=10, message = 'Longueur incorrect'),
                                                               Regexp(r'^\d{10}$', message="Le numéro de téléphone doit contenir uniquement des chiffres.")])
    name = StringField("Nom", validators=[DataRequired(), Length(max=32)])
    first_name = StringField("Prénom", validators=[DataRequired(), Length(max=32)])
    password = PasswordField("Mot de passe", validators=[DataRequired(), Length(max=64)])
    password_check = PasswordField("Confirmez votre mot de passe", validators=[DataRequired(), 
                                                                               EqualTo('password_check', message='Les mots de passe doivent correspondre'),])
    address = StringField("Adresse", validators=[DataRequired(), Length(max=64)])
    email = EmailField("Email", validators=[DataRequired(), Email(message='addresse mail invalide'), Length(max=64)])
    # Commentaire de la ligne en-dessous à enlever une fois le captcha mis en place 
    #recaptcha = RecaptchaField() 

    def get_authentificated_user(self):
        """permet de savoir si le mot de passe de 
        l'utilisateur est bon

        Returns:
            User: L'utilisateur si le mot de passe est correct, None sinon
        """
        user = User.query.get(self.phone_number.data)
        if user is None:
            return None
        m = sha256()
        m.update(self.password.data.encode())
        passwd = m.hexdigest()
        return user if passwd == user.mdp else None
    
    def create_user(self) :
        passwd = self.password.data
        m = sha256()
        m.update(passwd.encode())
        return User(num_tel=self.phone_number.data,
                 mdp=m.hexdigest(),
                 nom = self.name.data,
                 prenom = self.first_name.data,
                 adresse = self.address.data,
                 email = self.email.data)

@app.route("/connexion", methods = ("GET", "POST", ))
def login():
    f = LoginForm()
    if f.validate_on_submit():
        the_user = f.get_authentificated_user()
        if the_user:
            login_user(the_user)
            return redirect(url_for("home"))
        return render_template("connexion.html", form = f, error = 'incorrect_password')
    return render_template("connexion.html", form = f)

@app.route("/deconnexion")
def logout():
    logout_user()
    return redirect(url_for("accueil"))

@app.route("/inscription", methods = ["GET", "POST"])
def register():
    f = RegisterForm()
    if f.validate_on_submit():
        passwd = f.password.data
        passwd_2 = f.password_check.data
        if passwd != passwd_2 :
            print("mot de passe pas bon")
            return render_template("inscription.html", form = f, error="password_not_same")
        u = f.create_user()
        if User.query.get(u.get_id()) :
            return render_template("inscription.html", form = f, error="phone_number_already_exist")
        else :
            db.session.add(u)                  #
            db.session.commit()                # à enlever une fois le captcha mis en place
            login_user(u)                      #
            return redirect(url_for("home"))   #

        # à ajouter une fois le captcha mis en place
        """try :
            db.session.add(u)
            db.session.commit()
            return redirect(url_for("login"))
        except Exception :
            return render_template("inscription.html", form = f_erreur)"""
    print("test")
    return render_template("inscription.html", form = f)