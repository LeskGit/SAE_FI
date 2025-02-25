from wtforms import EmailField, StringField, TextAreaField
from project import app, db
from flask import render_template, url_for, redirect, request, flash
from project.app import mail
from flask_wtf import FlaskForm
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from flask_mail import Message

class ContactForm(FlaskForm):
    email = EmailField('Email')
    objet = StringField('Objet')
    message = TextAreaField('Message')

@app.route("/")
def home():
    images = ["img/slide-1.jpg", "img/slide-2.jpg", "img/slide-3.jpg", "img/quelques-plats-japonais.jpg"]
    return render_template("home.html",
                           images=images)

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

@app.route("/envoie_email", methods=['POST'])
def envoie_email() :
    form = ContactForm()
    if form.validate_on_submit() :
        objet = form.objet.data
        email = form.email.data
        message = form.message.data

        msg = Message(subject=objet, 
                      sender=email, 
                      recipients=['oumami.officiel@protonmail.com'] # à changer en l'adresse mail de la traiteuse
                      )
        msg.body=f"Email: {email}\nMessage: {message}"

        try:
            mail.send(msg)
            flash('Message envoyé', 'success')
        except Exception as e:
            flash('Erreur lors de l\'envoi du message. Veuillez réessayer plus tard.', 'danger')
            
        return redirect(url_for("contact"))