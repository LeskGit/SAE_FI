"""
Ce module configure l'application Flask, la base de données SQLAlchemy, 
le gestionnaire de sessions et le système de gestion des téléchargements.
"""

import os.path
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager
from project import auth

def mkpath(p):
    """
    Renvoie un chemin normalisé en joignant le chemin du fichier courant avec le chemin spécifié.

    Args:
        p (str): Le chemin à joindre.

    Returns:
        str: Le chemin normalisé.
    """
    return os.path.normpath(os.path.join(os.path.dirname(__file__), p))



app = Flask(__name__)
app.config['BOOSTRAP_SERVE_LOCAL'] = True
app.config['UPLOAD_FOLDER'] = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'static', 'img', 'product')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
bootstrap = Bootstrap5(app)

app.config['SECRET_KEY'] = '599ad302-c28b-49ae-9144-83c6f2eb081a'
app.config[
    'RECAPTCHA_PUBLIC_KEY'] = 'da0c592c-89e2-4d82-ac17-620b2c1d6226'  # à modifier en mettant un repcatcha Google une fois le serveur mis en place
app.config['RECAPTCHA_PRIVATE_KEY'] = app.config['SECRET_KEY']
app.config[
    'SQLALCHEMY_DATABASE_URI'] = f'mysql://{auth.nom}:{auth.mdp}@{auth.db}/DB{auth.nom}'

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
