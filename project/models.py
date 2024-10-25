from sqlalchemy import CheckConstraint, text
from sqlalchemy.orm import validates
from .app import db, login_manager
from flask_login import UserMixin
import re

class User(db.Model, UserMixin):
    num_tel = db.Column(db.String(10), CheckConstraint("LENGTH(num_tel) = 10 AND num_tel REGEXP '^[0-9]+$'"), primary_key = True)
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
        if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+.[A-Z|a-z]{2,}$", address):
            raise ValueError("Invalid email address")
        return address

@login_manager.user_loader
def load_user(num_tel):
    return User.query.get(num_tel)

contenir = db.Table("contenir",
    db.Column("nom", db.String(64), db.ForeignKey("plats.nom_plat"), primary_key=True),
    db.Column("id_formule", db.Integer, db.ForeignKey("formule.id_formule"), primary_key=True)
)

constituer = db.Table("constituer",
    db.Column("nom_plat", db.String(64), db.ForeignKey("plats.nom_plat"), primary_key=True),
    db.Column("num_commande", db.Integer, db.ForeignKey("commandes.num_commande"), primary_key=True),
    db.Column("quantite_plat", db.Integer, default=1)
)

class Commandes(db.Model):
    num_commande = db.Column(db.Integer, primary_key = True)
    num_tel = db.Column(db.String(10), db.ForeignKey("user.num_tel"))
    date = db.Column(db.DateTime)
    sur_place = db.Column(db.Boolean)
    num_table = db.Column(db.Integer, CheckConstraint("0 < num_table AND num_table <= 12"), unique = True)
    etat = db.Column(db.Enum("Panier", "Livraison", "Non payée", "Payée"))
    les_plats = db.relationship("Plats", secondary = constituer, back_populates = "les_commandes")
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
    les_commandes = db.relationship("Commandes", secondary = constituer, back_populates = "les_plats")
    les_formules = db.relationship("Formule", secondary = contenir, back_populates="les_plats")
    est_bento = db.Column(db.Boolean, default=False)

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
        self.execute_triggers()

    def execute_triggers(self) -> None:
        """
        Execute all trigger methods in the class.

        Trigger methods are methods that start with "trigger_".
        """
        for attr_name in dir(self):
            if attr_name.startswith("trigger_"):
                method = getattr(self, attr_name)
                if callable(method):
                    trigger_str = method()
                    db.session.execute(text(trigger_str))
                    db.session.commit()
    
    #TODO : Ne pas oublier le BEFORE UPDATE

    def trigger_test(self) -> str:
        return """
        CREATE OR REPLACE TRIGGER test BEFORE INSERT ON user FOR EACH ROW
        BEGIN
            IF NEW.num_tel = "0000000000" THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "Erreur : numéro de téléphone invalide";
            END IF;
        END;
        """

    def trigger_formule(self) -> str:
        """
        Trigger qui empêche de créer une formule avec plus de 4 plats
        """
        return """
        CREATE OR REPLACE TRIGGER nb_plat BEFORE INSERT ON contenir FOR EACH ROW
        BEGIN
            DECLARE nb INT;

            SELECT count(*) INTO nb 
            FROM contenir 
            WHERE id_formule = new.id_formule; 

            IF nb >= 4 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Une formule ne peut pas contenir plus de 4 plats';
            END IF;
        END;
        """
    
    def trigger_limiter_commandes_surplace(self) -> str:
        return """
        CREATE OR REPLACE TRIGGER limiter_commandes_surplace BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN
            DECLARE nb INT;

            SELECT count(*) INTO nb 
            FROM commandes 
            WHERE sur_place = 1; 

            IF nb >= 12 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Il y a déjà 12 commandes sur place';
            END IF;
        END;
        """
    
    def trigger_commandes_surplace_midi(self) -> str:
        return """
        CREATE OR REPLACE TRIGGER commandes_surplace_midi BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN
            IF HOUR(NEW.date) BETWEEN 12 AND 14 THEN
                IF NEW.sur_place = 1 THEN
                    SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'Impossible de commander sur place entre 12h et 14h';
                END IF;
            END IF;
        END;
        """
    
    def trigger_update_commande(self) -> str:
        """
        Trigger qui empêche de modifier une commande après 15 minutes après la date de la commande
        """
        return """
        CREATE OR REPLACE TRIGGER update_commande BEFORE UPDATE ON commandes FOR EACH ROW
        BEGIN
            DECLARE current_time DATETIME;
            SET current_time = NOW();

            IF TIMESTAMPDIFF(MINUTE, NEW.date, current_time) > 15 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Impossible de modifier une commande après 15 minutes';
            END IF;
        END;
        """
    
    def trigger_delete_commande(self) -> str:
        """
        Trigger qui empêche de supprimer une commande après 15 minutes après la date de la commande
        """
        return """
        CREATE OR REPLACE TRIGGER delete_commande BEFORE DELETE ON commandes FOR EACH ROW
        BEGIN
            DECLARE current_time DATETIME;
            SET current_time = NOW();

            IF TIMESTAMPDIFF(MINUTE, OLD.date, current_time) > 15 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Impossible de supprimer une commande après 15 minutes';
            END IF;
        END;
        """
    
    def trigger_reserver_delais(self) -> str:
        """
        Trigger qui empêche de réserver 2 heures avant la date de la commande
        """
        return """
        CREATE OR REPLACE TRIGGER reserver_delais BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN
            DECLARE current_time DATETIME;
            SET current_time = NOW();

            IF TIMESTAMPDIFF(HOUR, NEW.date, current_time) < 2 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Impossible de réserver moins de 2 heures avant la date de la commande';
            END IF;
        END;
        """
    
    def trigger_commande_non_payee(self) -> str:
        """
        Trigger qui empêche de commander si l'utilisateur a une commande non payée
        """
        return """
        CREATE OR REPLACE TRIGGER commande_non_payee BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN
            DECLARE nb INT;

            SELECT count(*) INTO nb 
            FROM commandes 
            WHERE num_tel = NEW.num_tel AND etat = 'Non payée'; 

            IF nb > 0 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Vous avez une commande non payée';
            END IF;
        END;
        """
    
    def trigger_commande_blacklisted(self) -> str:
        """
        Trigger qui empêche de commander si l'utilisateur est blacklisted
        """
        return """
        CREATE OR REPLACE TRIGGER commande_blacklisted BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN
            IF (SELECT blacklisted FROM user WHERE num_tel = NEW.num_tel) = 1 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Vous êtes blacklisted';
            END IF;
        END;
        """
    
    

def execute_tests():

    usr = User(num_tel = '0123456759',
                nom = 'Doe',
                prenom = 'John',
                password = 'password',
                adresse = '1 rue de la Paix',
                email = 'a@b.com',
                blacklisted = False,
                points_fidelite = 0,
                prix_panier = 0)
    
    db.session.add(usr)
    db.session.commit()


    #5 Plats
    plat1 = Plats(nom_plat = 'plat1',
                type_plat = 'Plat chaud',
                quantite_stock = 10,
                prix = 10,
                quantite_promo = 0,
                prix_reduc = 0)
    plat2 = Plats(nom_plat = 'plat2',
                type_plat = 'Plat froid',
                quantite_stock = 10,
                prix = 10,
                quantite_promo = 0,
                prix_reduc = 0)
    plat3 = Plats(nom_plat = 'plat3',
                type_plat = 'Sushi',
                quantite_stock = 10,
                prix = 10,
                quantite_promo = 0,
                prix_reduc = 0)
    plat4 = Plats(nom_plat = 'plat4',
                type_plat = 'Dessert',
                quantite_stock = 10,
                prix = 10,
                quantite_promo = 0,
                prix_reduc = 0)
    plat5 = Plats(nom_plat = 'plat5',
                type_plat = 'Plat chaud',
                quantite_stock = 10,
                prix = 10,
                quantite_promo = 0,
                prix_reduc = 0)
    
    db.session.add_all([plat1, plat2, plat3, plat4, plat5])

    #Formule
    formule1 = Formule(id_formule = 1,
                        libelle_formule = 'formule1',
                        prix = 20)
    
    db.session.add(formule1)
    
    formule1.les_plats.append(plat1)
    formule1.les_plats.append(plat2)
    formule1.les_plats.append(plat3)

    db.session.commit()