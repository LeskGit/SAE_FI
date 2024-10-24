from sqlalchemy import CheckConstraint
from .app import db, login_manager
from flask_login import UserMixin

class User(db.Model, UserMixin):
    num_tel = db.Column(db.String(10), CheckConstraint('LENGTH(num_tel) = 10'), primary_key=True)
    nom = db.Column(db.String(32))
    prenom = db.Column(db.String(32))
    password = db.Column(db.String(64))
    adresse = db.Column(db.String(64))
    email = db.Column(
        db.String(64), 
        CheckConstraint(r"email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'"), 
        unique=True
    )
    blacklisted = db.Column(db.Boolean, default=False)
    points_fidelite = db.Column(db.Integer, default=0)
    prix_panier = db.Column(db.Float, default=0)
    les_commandes = db.relationship("Commandes", back_populates = "les_clients")

@login_manager.user_loader
def load_user(num_tel):
    return User.query.get(num_tel)

contenir = db.Table('contenir',
    db.Column('nom', db.String(64), db.ForeignKey('Plats.nom_plat'), primary_key=True),
    db.Column('id_formule', db.Integer, db.ForeignKey('Formule.id_formule'), primary_key=True)
)

class Commandes(db.Model):
    num_commande = db.Column(db.Integer, primary_key = True)
    num_tel = db.Column(db.String(10), db.ForeignKey('User.num_tel'))
    date = db.Column(db.DateTime)
    sur_place = db.Column(db.Boolean)
    num_table = db.Column(db.Integer, CheckConstraint('0 < num_table AND num_table <= 12'))
    etat = db.Column(db.Enum("Panier", "Livraison", "Non payée", "Payée"))
    les_plats = db.relationship("Plats", back_populates = "les_commandes")
    les_clients = db.relationship("User", back_populates = "les_commandes")

    def __repr__(self):
        return f"{self.num_commande} : {self.date}"

class Plats(db.Model):
    nom_plat = db.Column(db.String(64), primary_key = True)
    type_plat = db.Column(db.Enum("Plat chaud", "Plat froid", "Sushi", "Dessert"))
    quantite_stock = db.Column(db.Integer)
    prix = db.Column(db.Float)
    quantite_promo = db.Column(db.Integer)
    prix_reduc = db.Column(db.Float)
    les_commandes = db.relationship("Commandes", back_populates = "les_plats")
    les_formules = db.relationship("Formule", secondary = contenir, back_populates = "les_plats")

    def __repr__(self):
        return f"{self.nom} ( {self.type_plat} ) : {self.prix}"

class Formule(db.Model):
    id_formule = db.Column(db.Integer, primary_key = True)
    libelle_formule = db.Column(db.String(64))
    prix = db.Column(db.Float)
    les_plats = db.relationship("Plats", secondary = contenir, back_populates = "les_formules")

    def __repr__(self):
        return f"{self.id_formule} : {self.libelle_formule}"







