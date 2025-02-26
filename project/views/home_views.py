from wtforms import EmailField, StringField, TextAreaField
from project import app, db
from flask import render_template, url_for, redirect, request, flash
from project.app import mail
from flask_wtf import FlaskForm
from flask_login import login_user, current_user, logout_user, login_required
from hashlib import sha256
from flask_mail import Message
from datetime import datetime



class ContactForm(FlaskForm):
    email = EmailField('Email')
    objet = StringField('Objet')
    message = TextAreaField('Message')


@app.route("/")
def home():
    images = [
        "img/slide-1.jpg", "img/slide-2.jpg", "img/slide-3.jpg",
        "img/quelques-plats-japonais.jpg"
    ]
    return render_template("home.html", images=images)


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
def envoie_email():
    if current_user.is_authentificated :
        form = ContactForm()
        if form.validate_on_submit():
            objet = form.objet.data
            email = current_user.email
            message = form.message.data

            text_body = f"""
    Message de contact - Restaurant Oumami

    De: {email}
    Objet: {objet}

    Message:
    {message}

    --
    Ce message a été envoyé depuis le formulaire de contact du site web Oumami.
    """

            # Version HTML pour un meilleur rendu
            html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4a4a4a; color: white; padding: 10px 20px; }}
            .content {{ padding: 20px; border: 1px solid #ddd; }}
            .footer {{ font-size: 12px; color: #777; margin-top: 20px; text-align: center; }}
            .field {{ margin-bottom: 15px; }}
            .field-label {{ font-weight: bold; }}
            .message-content {{ background-color: #f9f9f9; padding: 15px; border-left: 3px solid #4a4a4a; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Message de contact - Restaurant Oumami</h2>
            </div>
            <div class="content">
                <div class="field">
                    <p class="field-label">De:</p>
                    <p>{email}</p>
                </div>
                <div class="field">
                    <p class="field-label">Objet:</p>
                    <p>{objet}</p>
                </div>
                <div class="field">
                    <p class="field-label">Message:</p>
                    <div class="message-content">
                        {message.replace(chr(10), '<br>')}
                    </div>
                </div>
            </div>
            <div class="footer">
                <p>Ce message a été envoyé depuis le formulaire de contact du site web Oumami.</p>
                <p>© {datetime.now().year} Restaurant Oumami. Tous droits réservés.</p>
            </div>
        </div>
    </body>
    </html>
    """

            msg = Message(subject=f"[Contact Oumami] {objet}",
                        sender=("Formulaire Oumami", app.config['MAIL_USERNAME']),
                        recipients=['oumami.test@gmail.com'], # à modifier avec l'adresse mail de la traiteuse
                        reply_to=email)

            msg.body = text_body
            msg.html = html_body

            try:
                mail.send(msg)
                flash('Message envoyé', 'success')
            except Exception as e:
                app.logger.error(f"Erreur d'envoi d'email: {str(e)}")
                flash(
                    'Erreur lors de l\'envoi du message. Veuillez réessayer plus tard.',
                    'danger')
    else : 
        flash('Veillez vous connecter pour envoyer un e-mail.', 'danger')
    return redirect(url_for("contact"))
