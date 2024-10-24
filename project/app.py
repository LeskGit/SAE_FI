import os.path

from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager
import auth

def mkpath(p):
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), p))

app = Flask(__name__)
app.config['BOOSTRAP_SERVE_LOCAL'] = True
bootstrap = Bootstrap5(app)

app.config['SECRET_KEY'] = '599ad302-c28b-49ae-9144-83c6f2eb081a'

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{auth.nom}:{auth.mdp}@{auth.db}/DB{auth.nom}'

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'