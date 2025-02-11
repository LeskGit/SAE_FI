from project import app, db
from flask import render_template, url_for, redirect, request
from flask_wtf import FlaskForm, RecaptchaField
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from wtforms import StringField, PasswordField, EmailField
from wtforms.validators import DataRequired, EqualTo, Email, Length, Regexp, ValidationError
from wtforms.validators import DataRequired, EqualTo, Email, Length, Regexp, ValidationError
from project.models import User

class LoginForm (FlaskForm):
    phone_number = StringField("Numéro de téléphone", validators=[DataRequired(), 
                                                                  Length(min=10, max=10, message = 'Longueur incorrecte.'), 
                                                                  Regexp(r'^\d{10}$', message="Le numéro de téléphone est invalide.")])
    password = PasswordField("Mot de passe", validators=[DataRequired(), Length(max=64)])

    def get_authentificated_user(self):
        """permet de savoir si le mot de passe de 
        l'utilisateur est bon

        Returns:
            User: L'utilisateur si le mot de passe est correct, None sinon
        """
        user = User.get_user(self.phone_number.data)
        if user is None:
            return None
        m = sha256()
        m.update(self.password.data.encode())
        passwd = m.hexdigest()
        return user if passwd == user.mdp else None

class RegisterForm (FlaskForm):
    phone_number = StringField("Numéro téléphone", validators=[DataRequired(), 
                                                               Length(min=10, max=10, message = 'Longueur incorrecte.'),
                                                               Regexp(r'^\d{10}$', message="Le numéro de téléphone est invalide.")])
    name = StringField("Nom", validators=[DataRequired(), 
                                          Length(max=32)])
                                          
                                          
    first_name = StringField("Prénom", validators=[DataRequired(), 
                                                   Length(max=32)])

    email = EmailField("Email", validators=[DataRequired(), Email(message='Adresse mail invalide.'), 
                                            Length(max=64)])

    address = StringField("Adresse", validators=[DataRequired(), Length(max=64)])

    password = PasswordField("Mot de passe", validators=[DataRequired(), 
                                                         Length(max=64)])

    password_check = PasswordField("Confirmez votre mot de passe", validators=[DataRequired(), 
                                                                               EqualTo('password', message='Les mots de passe doivent correspondre.'),])

    # Commentaire de la ligne en-dessous à enlever une fois le captcha mis en place 
    #recaptcha = RecaptchaField() 

    def validate_email(self, field):
        if User.check_user_email(email_u=field.data):
            raise ValidationError("Cet e-mail est déjà utilisé.")

    def validate_phone_number(self, field):
        if User.check_user_num(num_tel_u=field.data):
            raise ValidationError("Ce numéro de téléphone est déjà utilisé.")

    def get_authentificated_user(self):
        """permet de savoir si le mot de passe de 
        l'utilisateur est bon

        Returns:
            User: L'utilisateur si le mot de passe est correct, None sinon
        """
        user = User.get_user(self.phone_number.data)
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
        return render_template("connexion.html", form = f, error = 'Mot de passe incorrect.')
    return render_template("connexion.html", form = f)

@app.route("/deconnexion")
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/inscription", methods = ["GET", "POST"])
def register():
    f = RegisterForm()
    if f.validate_on_submit():
        u = f.create_user()
        if User.query.get(u.get_id()) :
            return render_template("inscription.html", form = f)
        else :
            db.session.add(u)                  #
            db.session.commit()                # à enlever une fois le captcha mis en place
            login_user(u)                      #
            return redirect(url_for("home"))   #

        # à ajouter une fois le captcha mis en place
        """try :
            if User.query.get(u.get_id()) :
                return render_template("inscription.html", form = f)
            else :
                db.session.add(u)
                db.session.commit()
                login_user(u)
                return redirect(url_for("home"))
        except Exception :
            return render_template("inscription.html", form = f)
            db.session.rollback()"""
    return render_template("inscription.html", form = f)