import os.path

from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager

def mkpath(p):
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), p))

app = Flask(__name__)
app.config['BOOSTRAP_SERVE_LOCAL'] = True
bootstrap = Bootstrap5(app)

app.config['SECRET_KEY'] = 'b19d7fe4-604e-46fb-a701-6c6f51e9676d'   ## Utilisé pour les formulaires => CSRF protection (Cross-Site Request Forgery) => protection contre les attaques CSRF => token de session => vérification de l'origine de la requête (le token est généré par le serveur et envoyé au client, le client doit le renvoyer pour chaque requête)
                                                                    ##on s'assure que la requête provient bien de notre site
app.config['SQLALCHEMY_DATABASE_URI'] = ('sqlite:///' + mkpath('../oumami.db'))
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'