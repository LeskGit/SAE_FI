from sqlalchemy import CheckConstraint, text
from sqlalchemy.orm import validates
from .app import db, login_manager
from flask_login import UserMixin
import re

class User(db.Model, UserMixin):
    num_tel = db.Column(db.String(10), CheckConstraint("LENGTH(num_tel) = 10"), primary_key=True)
    nom = db.Column(db.String(32))
    prenom = db.Column(db.String(32))
    password = db.Column(db.String(64))
    adresse = db.Column(db.String(64))
    email = db.Column(
        db.String(64),
        unique=True
    )
    blacklisted = db.Column(db.Boolean, default=False)
    points_fidelite = db.Column(db.Integer, default=0)
    prix_panier = db.Column(db.Float, default=0)
    les_commandes = db.relationship("Commandes", back_populates = "les_clients")

    @validates("email")
    def validate_email(self, key, address):
        if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$", address):
            raise ValueError("Invalid email address")
        return address

@login_manager.user_loader
def load_user(num_tel):
    return User.query.get(num_tel)

contenir = db.Table("contenir",
    db.Column("nom", db.String(64), db.ForeignKey("plats.nom_plat"), primary_key=True),
    db.Column("id_formule", db.Integer, db.ForeignKey("formule.id_formule"), primary_key=True)
)

class Commandes(db.Model):
    num_commande = db.Column(db.Integer, primary_key = True)
    num_tel = db.Column(db.String(10), db.ForeignKey("user.num_tel"))
    date = db.Column(db.DateTime)
    sur_place = db.Column(db.Boolean)
    num_table = db.Column(db.Integer, CheckConstraint("0 < num_table AND num_table <= 12"))
    etat = db.Column(db.Enum("Panier", "Livraison", "Non payée", "Payée"))
    les_plats = db.relationship("Plats", back_populates = "les_commandes")
    plats = db.relationship("Plats", secondary="contenir", back_populates="formules")

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
    formules = db.relationship("Formule", secondary="contenir", back_populates="plats")

    def __repr__(self):
        return f"{self.nom_plat} ({self.type_plat}) : {self.prix}"

class Formule(db.Model):
    id_formule = db.Column(db.Integer, primary_key = True)
    libelle_formule = db.Column(db.String(64))
    prix = db.Column(db.Float)
    les_plats = db.relationship("Plats", secondary = contenir, back_populates = "les_formules")

    def __repr__(self):
        return f"{self.id_formule} : {self.libelle_formule}"

#--------

class TriggerManager:

    def __init__(self):
        self.trigger_test()
        self.trigger_formule()

    def trigger_test(self):
        db.session.execute(text("""
        CREATE or replace TRIGGER test BEFORE INSERT ON user
        FOR EACH ROW
        BEGIN
            IF NEW.num_tel = "0000000000" THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "Erreur : numéro de téléphone invalide";
            END IF;
        END;
        """))
        db.session.commit()

    def trigger_formule(self):
        db.engine.execute(text("""
        CREATE OR REPLACE TRIGGER nb_plat BEFORE INSERT ON contenir FOR EACH ROW
        BEGIN
            DECLARE nb int;

            Select count(*) into nb 
            FROM contenir 
            WHERE id_formule = new.id_formule; 

            IF nb > 4 then
                SIGNAL SQLstate '45000'
                SET MESSAGE_TEXT = 'Une formule ne peut pas contenir plus de 4 plats'
            END IF;
        END;
        """))
        db.session.commit()