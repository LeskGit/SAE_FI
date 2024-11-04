import os.path

from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_bootstrap import Bootstrap5

def mkpath(p):
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), p))

app = Flask(__name__)
app.config['BOOSTRAP_SERVE_LOCAL'] = True
bootstrap = Bootstrap5(app)

                                                                    ##on s'assure que la requête provient bien de notre site
app.config['SQLALCHEMY_DATABASE_URI'] = ('sqlite:///' + mkpath('../oumami.db'))
db = SQLAlchemy(app)

