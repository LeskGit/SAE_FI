from flask import Flask
from flask_bootstrap import Bootstrap5
import os.path
from flask import app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
bootstrap = Bootstrap5(app)

def mkpath(p):
    return os.path.normpath(
        os.path.join(
            os.path.dirname(__file__),
            p))

app.config['SQLALCHEMY_DATABASE_URI'] = (
    'sqlite:///'+mkpath('../tuto.db'))
db = SQLAlchemy(app)