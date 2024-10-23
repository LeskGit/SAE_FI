from sqlalchemy import CheckConstraint
from .app import db, login_manager
from flask_login import UserMixin

class User(db.Model, UserMixin):
    num_tel = db.Column(db.String(10), CheckConstraint('LENGTH(num_tel) = 10'), primary_key=True)
    nom = db.Column(db.String(32))
    prenom = db.Column(db.String(32))
    password = db.Column(db.String(64))
    adresse = db.Column(db.String(64))
    email = db.Column(db.String(64), CheckConstraint("email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'"), unique=True)
    blacklisted = db.Column(db.Boolean, default=False)
    points_fidelite = db.Column(db.Integer, default=0)
    prix_panier = db.Column(db.Float, default=0)

@login_manager.user_loader
def load_user(num_tel):
    return User.query.get(num_tel)