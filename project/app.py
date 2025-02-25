import os.path

from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager
from flask_mail import Mail
import project.auth as auth

def mkpath(p):
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), p))
    
    

app = Flask(__name__)
app.config['BOOSTRAP_SERVE_LOCAL'] = True
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'img', 'product')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
bootstrap = Bootstrap5(app)

app.config['SECRET_KEY'] = '599ad302-c28b-49ae-9144-83c6f2eb081a'
app.config['RECAPTCHA_PUBLIC_KEY'] = 'da0c592c-89e2-4d82-ac17-620b2c1d6226'  # à modifier en mettant un repcatcha Google une fois le serveur mis en place
app.config['RECAPTCHA_PRIVATE_KEY'] = app.config['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{auth.nom}:{auth.mdp}@{auth.db}/DB{auth.nom}'

app.config['MAIL_SERVER'] = 'smtp.protonmail.ch'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'oumami.serveur@protonmail.com'
app.config['MAIL_PASSWORD'] = 'OUmami01!02040406'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

db = SQLAlchemy(app)


login_manager = LoginManager(app)
login_manager.login_view = 'login'