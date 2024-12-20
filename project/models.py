from sqlalchemy import CheckConstraint, text
from sqlalchemy.orm import validates
from .app import db, login_manager
from flask_login import UserMixin
import re
from datetime import date, datetime, timedelta
from hashlib import sha256

class User(db.Model, UserMixin):
    num_tel = db.Column(db.String(10), CheckConstraint("LENGTH(num_tel) = 10 AND num_tel REGEXP '^[0-9]+$'"), primary_key = True)
    nom = db.Column(db.String(32))
    prenom = db.Column(db.String(32))
    mdp = db.Column(db.String(64))
    adresse = db.Column(db.String(64))
    email = db.Column(
        db.String(64),
        unique=True
    )
    blackliste = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default = False)
    points_fidelite = db.Column(db.Integer, default=0)
    les_commandes = db.relationship("Commandes", back_populates = "les_clients")

    @validates("email")
    def validate_email(self, key, address):
        if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+.[A-Z|a-z]{2,}$", address):
            raise ValueError("Invalid email address")
        return address
    
    def get_id(self):
        return self.num_tel

    def get_panier(self):
        panier = Commandes.query.filter_by(num_tel = self.num_tel, etat = "Panier").first()
        return panier
    
    def get_or_create_panier(self):
        panier = self.get_panier()
        if panier is None:
            panier = Commandes(num_tel=self.num_tel, etat="Panier")
            db.session.add(panier)
            db.session.commit()
        return panier

@login_manager.user_loader
def load_user(num_tel):
    return User.query.get(num_tel)

CONTENIR_NOM_PLAT = "plats.nom_plat"

contenir = db.Table("contenir",
    db.metadata,
    db.Column("nom", db.String(64), db.ForeignKey(CONTENIR_NOM_PLAT), primary_key=True),
    db.Column("id_formule", db.Integer, db.ForeignKey("formule.id_formule"), primary_key=True)
)

class Constituer(db.Model):
    __tablename__ = "constituer"
    nom_plat = db.Column(db.String(64), db.ForeignKey(CONTENIR_NOM_PLAT), primary_key=True)
    num_commande = db.Column(db.Integer, db.ForeignKey("commandes.num_commande"), primary_key=True)
    quantite_plat = db.Column(db.Integer, default=1)
    plat = db.relationship("Plats", back_populates="constituer_assoc", overlaps="les_commandes,commande")
    commande = db.relationship("Commandes", back_populates="constituer_assoc", overlaps="les_plats,plat")

class Commandes(db.Model):
    num_commande = db.Column(db.Integer, primary_key=True, autoincrement=True)
    num_tel = db.Column(db.String(10), db.ForeignKey("user.num_tel"))
    date = db.Column(db.DateTime)
    date_creation = db.Column(db.DateTime, default = db.func.current_timestamp())
    sur_place = db.Column(db.Boolean, default = False)
    num_table = db.Column(db.Integer, CheckConstraint("0 < num_table AND num_table <= 12"))
    etat = db.Column(db.Enum("Panier", "Non payée", "Payée"), default = "Panier")

    les_plats = db.relationship("Plats", secondary = "constituer", back_populates = "les_commandes", overlaps="constituer_assoc,plat")
    les_clients = db.relationship("User", back_populates="les_commandes")
    constituer_assoc = db.relationship("Constituer", back_populates="commande", overlaps="les_plats,plat")

    prix_total = 0
    prix_avec_reduc = 0

    def __repr__(self):
        return f"{self.num_commande} : {self.date}"
    
    def calculer_prix(self):
        self.prix_total = sum([constituer.plat.prix * constituer.quantite_plat for constituer in self.constituer_assoc])
        return self.prix_total

    def compute_reduction(self):
        """
        Calcule la réduction de la commande :
        Applique le prix - prix_reduc pour chaque plat en promotion (constituer.quantite_plat > quantite_promo)
        """
        self.prix_avec_reduc = 0
        for constituer in self.constituer_assoc:
            if constituer.quantite_plat >= constituer.plat.quantite_promo:
                self.prix_avec_reduc -= constituer.plat.prix_reduc
        return self.prix_avec_reduc
    
    def get_num_table_dispo(self):
        return 

class Plats(db.Model):
    nom_plat = db.Column(db.String(64), primary_key = True)
    type_plat = db.Column(db.Enum("Plat chaud", "Plat froid", "Sushi", "Dessert"))
    stock_utilisable = db.Column(db.Integer)
    stock_reserve = db.Column(db.Integer)
    quantite_defaut = db.Column(db.Integer)
    prix = db.Column(db.Float)
    quantite_promo = db.Column(db.Integer)
    prix_reduc = db.Column(db.Float)
    est_bento = db.Column(db.Boolean, default=False)
    img = db.Column(db.String(200))

    les_formules = db.relationship("Formule", secondary = contenir, back_populates="les_plats")

    les_commandes = db.relationship("Commandes", secondary = 'constituer', back_populates = "les_plats", overlaps="constituer_assoc,commande")
    constituer_assoc = db.relationship("Constituer", back_populates="plat", overlaps="les_commandes,commande")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.stock_utilisable is not None:
            self.stock_reserve = int(self.stock_utilisable * 0.2)

    def __repr__(self):
        return f"{self.nom_plat} ({self.type_plat}) : {self.prix}"
    
    def get_all_plats(self):

        """ retourne tous les plats


        Returns:
            List[self]: une liste de plats
        """
        return self.query.all() 

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

    def trigger_limiter_commandes_sur_place_insert(self) -> str:
        """
        On ne peut avoir que 12 commandes sur place en même temps
        """
        return """
        CREATE TRIGGER limiter_commandes_sur_place_insert BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN
            DECLARE nb INT;

            SELECT count(*) INTO nb 
            FROM commandes
            WHERE sur_place = 1 and DATE(date) = DATE(NEW.date); 

            IF nb >= 12 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Il y a déjà 12 commandes sur place';
            END IF;
        END;
        """

    def trigger_limiter_commandes_sur_place_update(self) -> str:
        """
        On ne peut avoir que 12 commandes sur place en même temps
        """
        return """
        CREATE TRIGGER limiter_commandes_sur_place_update BEFORE UPDATE ON commandes FOR EACH ROW
        BEGIN
            DECLARE nb INT;

            SELECT count(*) INTO nb 
            FROM commandes
            WHERE sur_place = 1 and num_commande != NEW.num_commande and DATE(date) = DATE(NEW.date); 

            IF NEW.sur_place = 1 THEN
                IF nb >= 12 THEN
                    SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'Il y a déjà 12 commandes sur place';
                END IF;
            END IF;
        END;
        """

    def trigger_commandes_sur_place_midi_insert(self) -> str:
        """
        Permet de réserver une table uniquement le midi
        """
        return """
        CREATE TRIGGER commandes_sur_place_midi_insert BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN
            IF NOT (HOUR(NEW.date) = 11 AND MINUTE(NEW.date) >= 30 OR HOUR(NEW.date) BETWEEN 12 AND 13 OR HOUR(NEW.date) = 14 AND MINUTE(NEW.date) = 0) THEN
                IF NEW.sur_place = 1 THEN
                    SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'Impossible de commander sur place avant 11h30 et après 14h';
                END IF;
            END IF;
        END;
        """

    def trigger_commandes_sur_place_midi_update(self) -> str:
        """
        Permet de réserver une table uniquement le midi
        """
        return """
        CREATE TRIGGER commandes_sur_place_midi_update BEFORE UPDATE ON commandes FOR EACH ROW
        BEGIN
            IF NOT (HOUR(NEW.date) = 11 AND MINUTE(NEW.date) >= 30 OR HOUR(NEW.date) BETWEEN 12 AND 13 OR HOUR(NEW.date) = 14 AND MINUTE(NEW.date) = 0) THEN
                IF NEW.sur_place = 1 THEN
                    SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'Impossible de commander sur place avant 11h30 et après 14h';
                END IF;
            END IF;
        END;
        """

    def trigger_update_commande(self) -> str:
        """
        Trigger qui empêche de modifier une commande après 15 minutes après la date de la commande
        """
        return """
        CREATE TRIGGER update_commande BEFORE UPDATE ON commandes FOR EACH ROW
        BEGIN
            DECLARE current DATETIME DEFAULT NOW();

            IF TIMESTAMPDIFF(MINUTE, OLD.date_creation, current) > 15 and OLD.etat != 'Panier' THEN
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
        CREATE TRIGGER delete_commande BEFORE DELETE ON commandes FOR EACH ROW
        BEGIN
            DECLARE current DATETIME DEFAULT NOW();


            IF TIMESTAMPDIFF(MINUTE, OLD.date_creation, current) > 15 and OLD.etat != 'Panier' THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Impossible de supprimer une commande après 15 minutes';
            END IF;
        END;
        """

    def trigger_reserver_delais_insert(self) -> str:
        """
        Trigger qui empêche de réserver 2 heures avant la date de la commande
        """
        return """
        CREATE TRIGGER reserver_delais_insert BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN

            IF TIMESTAMPDIFF(HOUR, NEW.date_creation, NEW.date) < 2 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "Vous ne pouvez pas réserver moins de 2 heures à l'avance";
            END IF;
        END;
        """
    
    def trigger_reserver_delais_update(self) -> str:
        """
        Trigger qui empêche de réserver 2 heures avant la date de la commande
        """
        return """
        CREATE TRIGGER reserver_delais_update BEFORE UPDATE ON commandes FOR EACH ROW
        BEGIN

            IF TIMESTAMPDIFF(HOUR, NEW.date_creation, NEW.date) < 2 AND NEW.etat != 'Panier' THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Impossible de réserver moins de 2 heures avant la date de la commande';
            END IF;
        END;
        """

    #def trigger_commande_non_payee(self) -> str:
    #    """
    #    Trigger qui empêche de commander si l'utilisateur a une commande non payée
    #    """
    #    return """
    #    CREATE TRIGGER commande_non_payee BEFORE INSERT ON commandes FOR EACH ROW
    #    BEGIN
    #        DECLARE nb INT;##

    #        SELECT count(*) INTO nb 
    #        FROM commandes 
    #        WHERE num_tel = NEW.num_tel AND etat = 'Non payée'; 

    #        IF nb > 0 THEN
    #            SIGNAL SQLSTATE '45000'
    #            SET MESSAGE_TEXT = 'Vous avez une commande non payée';
    #        END IF;
    #    END;
    #    """

    def trigger_commande_blacklisted_insert(self) -> str:
        """
        Trigger qui empêche de commander si l'utilisateur est blackliste
        """
        return """
        CREATE TRIGGER commande_blacklisted_insert BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN
            IF (SELECT blackliste FROM user WHERE num_tel = NEW.num_tel) = 1 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Vous êtes blackliste';
            END IF;
        END;
        """

    def trigger_commande_blacklisted_update(self) -> str:
        """
        Trigger qui empêche de commander si l'utilisateur est blackliste
        """
        return """
        CREATE TRIGGER commande_blacklisted_update BEFORE UPDATE ON commandes FOR EACH ROW
        BEGIN
            IF (SELECT blackliste FROM user WHERE num_tel = NEW.num_tel) = 1 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Vous êtes blackliste';
            END IF;
        END;
        """

    def trigger_black_list_insert(self) -> str:
        """
        Trigger qui ajoute un utilisateur à la blacklist s'il n'est pas 
            venu chercher sa commande
        """
        return """
        CREATE TRIGGER black_list_insert BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN
            DECLARE temps INT;
            DECLARE current DATETIME DEFAULT NOW();

            SELECT max((TIMESTAMPDIFF(HOUR, current, date))) INTO temps 
            FROM commandes NATURAL JOIN user
            WHERE num_tel = NEW.num_tel AND etat = 'Non payée';

            IF temps >= 24 THEN
                UPDATE user
                SET blackliste = True
                WHERE num_tel = NEW.num_tel;
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Vous êtes blacklisté et ne pouvez plus commander';
            END IF;
        END;
        """

    def trigger_black_list_insert_update(self) -> str:
        """
        Trigger qui ajoute un utilisateur à la blacklist s'il n'est pas 
            venu chercher sa commande
        """
        return """
        CREATE TRIGGER black_list_update BEFORE UPDATE ON commandes FOR EACH ROW
        BEGIN
            DECLARE temps INT;
            DECLARE current DATETIME DEFAULT NOW();

            SELECT max((TIMESTAMPDIFF(HOUR, current, date))) INTO temps 
            FROM commandes NATURAL JOIN user
            WHERE num_tel = NEW.num_tel AND etat = 'Non payée';

            IF temps >= 24 THEN
                UPDATE user
                SET blackliste = True
                WHERE num_tel = NEW.num_tel;
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Vous êtes blacklisté et ne pouvez plus commander';
            END IF;
        END;
        """

    def trigger_stocks_insert(self) -> str:
        """
        Trigger qui vérifie si il reste assez de plats
            en stock
        """
        return """
        CREATE TRIGGER trigger_stocks_insert BEFORE INSERT ON constituer FOR EACH ROW
        BEGIN
            DECLARE stocks_u INT;
            DECLARE stocks_r INT;

            SELECT stock_utilisable, stock_reserve into stocks_u, stocks_r
            FROM plats
            WHERE nom_plat = NEW.nom_plat;

            IF stocks_u - NEW.quantite_plat < stocks_r THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "Le plat que vous souhaitez n'est plus en stock";
            END IF;
        END;
        """

    def trigger_plats_stocks_update(self) -> str:
        """
        Trigger qui vérifie si il reste assez de plats en stock
        """
        return """
        CREATE TRIGGER trigger_plats_stocks_update BEFORE UPDATE ON plats FOR EACH ROW
        BEGIN
            DECLARE stocks_u INT;
            DECLARE stocks_r INT;

            SELECT stock_utilisable, stock_reserve into stocks_u, stocks_r
            FROM plats
            WHERE nom_plat = NEW.nom_plat;

            IF NEW.stock_utilisable < NEW.stock_reserve THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "Le plat que vous souhaitez n'est plus en stock.";
            END IF;
        END;
        """

    def trigger_stocks_update(self) -> str:
        """
        Trigger qui vérifie si il reste assez de plats
            en stock
        """
        return """
        CREATE TRIGGER trigger_stocks_update BEFORE UPDATE ON constituer FOR EACH ROW
        BEGIN
            DECLARE stocks_u INT;
            DECLARE stocks_r INT;

            SELECT stock_utilisable, stock_reserve into stocks_u, stocks_r
            FROM plats
            WHERE nom_plat = NEW.nom_plat;

            IF stocks_u - NEW.quantite_plat < stocks_r THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "Le plat que vous souhaitez n'est plus en stock";
            END IF;
        END;
        """

    def trigger_table_insert(self) -> str:
        """
        On ne peut réserver une table que si elle est disponible
        """
        return """
        CREATE TRIGGER trigger_table_insert BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN
            DECLARE num INT;

            IF (NEW.sur_place = 0 AND NEW.num_table IS NOT NULL) OR (NEW.sur_place = 1 AND NEW.num_table IS NULL) THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "Il faut remplir 2 champs pour pouvoir réserver une table";
            END IF;

            SELECT num_commande into num
            FROM commandes
            WHERE num_table = NEW.num_table and date = NEW.date;

            IF num IS NOT NULL THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "La table est déjà occupée";
            END IF;
        END;
        """

    def trigger_table_update(self) -> str:
        """
        On ne peut réserver une table que si elle est disponible
        """
        return """
        CREATE TRIGGER trigger_table_update BEFORE UPDATE ON commandes FOR EACH ROW
        BEGIN
            DECLARE num INT;

            IF (NEW.sur_place = 0 AND NEW.num_table IS NOT NULL) OR (NEW.sur_place = 1 AND NEW.num_table IS NULL) THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "Il faut remplir 2 champs pour pouvoir réserver une table";
            END IF;

            SELECT num_commande into num
            FROM commandes
            WHERE num_table = NEW.num_table and date = NEW.date and num_commande != NEW.num_commande;

            IF num IS NOT NULL THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "La table est déjà occupée";
            END IF;
        END;
        """

    def trigger_formule_insert(self) -> str:
        """
        Une formule doit être constituée d'au maximum 4 produits de 
            catégories différentes
        """
        return """
        CREATE TRIGGER trigger_formule_insert BEFORE INSERT ON contenir FOR EACH ROW
        BEGIN
            DECLARE nombre int;
            DECLARE type VARCHAR(62);
            DECLARE n VARCHAR(62);

            SELECT count(nom) into nombre
            FROM contenir
            WHERE id_formule = NEW.id_formule;

            IF nombre > 3 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "La formule est déjà complète";
            END IF;

            SELECT type_plat into type
            FROM plats
            WHERE nom_plat = NEW.nom;

            SELECT nom into n
            FROM contenir
            WHERE nom in (
            SELECT nom_plat
            FROM plats
            WHERE type_plat = type) and id_formule = NEW.id_formule;

            IF n IS NOT NULL THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "La formule contient déjà ce type de plat";
            END IF;
        END;
        """

    def trigger_formule_update(self) -> str:
        """
        Une formule doit être constituée d'au maximum 4 produits de 
            catégories différentes
        """
        return """
        CREATE TRIGGER trigger_formule_update BEFORE UPDATE ON contenir FOR EACH ROW
        BEGIN
            DECLARE cnt INT DEFAULT 0;

            SELECT COUNT(*) INTO cnt
            FROM contenir c
            JOIN plats p ON c.nom = p.nom_plat
            WHERE c.id_formule = NEW.id_formule
            AND p.type_plat = (SELECT type_plat FROM plats WHERE nom_plat = NEW.nom)
            AND c.nom != OLD.nom;

            IF cnt > 0 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "La formule contient déjà ce type de plat";
            END IF;
        END;
        """

    def trigger_panier_insert(self) -> str:
        """
        Un utilisateur doit avoir un seul et unique panier en même temps
        """
        return """
        CREATE TRIGGER trigger_panier_insert BEFORE insert ON commandes FOR EACH ROW
        BEGIN
            DECLARE id INT;

            IF NEW.etat = "Panier" THEN
                SELECT etat into id FROM commandes
                WHERE num_tel = NEW.num_tel and
                etat = "Panier";

                IF id IS NOT NULL THEN
                    SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = "On ne peut avoir qu'un panier à la fois";
                END IF;
            END IF;
        END
        """

    def trigger_ferme_insert(self) -> str:
        """
        Impossible de faire des commandes le lundi ou dimanche
        """
        return """
        CREATE TRIGGER ferme_insert BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN
            IF DAYOFWEEK(NEW.date) IN (1, 2) THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Impossible de commander le lundi ou le dimanche';
            END IF;
        END;
        """

    def trigger_ferme_update(self) -> str:
        """
        Impossible de faire des commandes le lundi ou dimanche
        """
        return """
        CREATE TRIGGER ferme_update BEFORE UPDATE ON commandes FOR EACH ROW
        BEGIN
            IF DAYOFWEEK(NEW.date) IN (1, 2) THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Impossible de commander le lundi ou le dimanche';
            END IF;
        END;
        """

def execute_tests():

    password = "password"
    m = sha256()
    m.update(password.encode())
    hashed_password = m.hexdigest()

    usr = User(num_tel = '0123456759',
                nom = 'Doe',
                prenom = 'John',
                mdp = hashed_password,
                adresse = '1 rue de la Paix',
                email = 'a@b.com',
                blackliste = False,
                points_fidelite = 0)
    
    db.session.add(usr)
    db.session.commit()

    #5 Plats
    plat1 = Plats(nom_plat = 'plat1',
                type_plat = 'Plat chaud',
                stock_utilisable = 10,
                quantite_defaut = 7,
                prix = 10,
                quantite_promo = 2,
                prix_reduc = 10,
                img = 'sushi.jpg')
    plat2 = Plats(nom_plat = 'plat2',
                type_plat = 'Plat froid',
                stock_utilisable = 10,
                quantite_defaut = 6,
                prix = 10,
                quantite_promo = 0,
                prix_reduc = 0,
                img = 'sushi.jpg')
    plat3 = Plats(nom_plat = 'plat3',
                type_plat = 'Sushi',
                stock_utilisable = 10,
                quantite_defaut = 8,
                prix = 10,
                quantite_promo = 0,
                prix_reduc = 0,
                img = 'sushi.jpg')
    plat4 = Plats(nom_plat = 'plat4',
                type_plat = 'Dessert',
                stock_utilisable = 10,
                quantite_defaut = 12,
                prix = 10,
                quantite_promo = 0,
                prix_reduc = 0,
                img = 'sushi.jpg')
    plat5 = Plats(nom_plat = 'plat5',
                type_plat = 'Plat chaud',
                stock_utilisable = 10,
                quantite_defaut = 18,
                prix = 10,
                quantite_promo = 0,
                prix_reduc = 0,
                img = 'sushi.jpg')
    
    db.session.add_all([plat1, plat2, plat3, plat4, plat5])


    #Formule
    formule1 = Formule(id_formule = 1,
                        libelle_formule = 'formule1',
                        prix = 20)
    
    db.session.add(formule1)

    com1 = Commandes(num_tel = '0123456759',
                        date = datetime(2024, 11, 6, 12),
                        date_creation = datetime(2024, 11, 6),
                        sur_place = True,
                        num_table = 1,
                        etat = "Payée")

    com2 = Commandes(num_tel = '0123456759',
                        date = datetime(2024, 11, 5, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = True,
                        num_table = 2,
                        etat = "Payée")

    com3 = Commandes(num_tel = '0123456759',
                        date = datetime(2024, 11, 6, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = True,
                        num_table = 3,
                        etat = "Payée")

    com4 = Commandes(num_tel = '0123456759',
                        date = datetime(2024, 11, 5, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = True,
                        num_table = 4,
                        etat = "Payée")

    com5 = Commandes(num_tel = '0123456759',
                        date = datetime(2024, 11, 6, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = True,
                        num_table = 5,
                        etat = "Payée")

    com6 = Commandes(num_tel = '0123456759',
                        date = datetime(2024, 11, 5, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = True,
                        num_table = 6,
                        etat = "Payée")

    com7 = Commandes(num_tel = '0123456759',
                        date = datetime(2024, 11, 6, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = False,
                        num_table = None,
                        etat = "Payée")

    com8 = Commandes(num_tel = '0123456759',
                        date = datetime(2024, 11, 5, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = True,
                        num_table = 8,
                        etat = "Payée")

    com9 = Commandes(num_tel = '0123456759',
                        date = datetime(2024, 11, 6, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = True,
                        num_table = 9,
                        etat = "Payée")

    com10 = Commandes(num_tel = '0123456759',
                        date = datetime(2024, 11, 5, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = True,
                        num_table = 10,
                        etat = "Payée")

    com11 = Commandes(num_tel = '0123456759',
                        date = datetime(2024, 11, 6, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = True,
                        num_table = 11,
                        etat = "Payée")

    com12 = Commandes(num_tel = '0123456759',
                        date = datetime(2024, 11, 5, 12),
                        date_creation = datetime(2024, 11, 4, 10),
                        sur_place = True,
                        num_table = 12,
                        etat = "Panier")

    com13 = Commandes(num_tel = '0123456759',
                        date = datetime(2024, 11, 6, 13),
                        date_creation = datetime(2024, 11, 4, 10),
                        sur_place = True,
                        num_table = 12,
                        etat = "Non Payée")
    
    com13 = Commandes(num_tel = '0123456759',
                        date = datetime(2024, 12, 18, 13),
                        date_creation = datetime(2024, 12, 18, 10, 5),
                        sur_place = False,
                        etat = "Panier")

    db.session.add_all([com1, com2, com3, com4, com5, com6, com7, com8, com9, com10, com11, com12, com13])

    db.session.commit()

    commande = Commandes.query.get(1)

    try:
        # Ajouter des plats à Constituer pour la commande
        constituer_assoc = [
            Constituer(nom_plat='plat1', num_commande=commande.num_commande, quantite_plat=2),
            Constituer(nom_plat='plat2', num_commande=commande.num_commande, quantite_plat=3),
            Constituer(nom_plat='plat3', num_commande=commande.num_commande, quantite_plat=1)
        ]
        db.session.add_all(constituer_assoc)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Erreur:", e)

    try:
        formule1.les_plats.append(plat1)
        formule1.les_plats.append(plat2)
        formule1.les_plats.append(plat4)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Erreur:", e)

    db.session.commit()

def get_plats():
    return Plats.query.all()

def get_formules():
    return Formule.query.all()

def get_desserts():
    return  Plats.query.filter_by(type_plat = "Dessert").all()

def get_plats_chauds():
    return  Plats.query.filter_by(type_plat = "Plat chaud").all()

def get_plats_froids():
    return  Plats.query.filter_by(type_plat = "Plat froid").all()

def get_sushis():
    return  Plats.query.filter_by(type_plat = "Sushi").all()

def get_sur_place_at(date=datetime.today().date()):
    return Commandes.query.filter(db.func.date(Commandes.date) == date, Commandes.sur_place.is_(True)).all()
 
def get_num_table_dispo(commande_date:datetime):
    """Renvoie le numéro de la première table disponible
    """
    commandes_sur_place = get_sur_place_at(commande_date.date())

    dico_tables = {i: False for i in range(1, 13)}
    for table in commandes_sur_place:
        dico_tables[table.num_table] = True
    
    for num_table, occupe in dico_tables.items():
        if not occupe:
            return num_table
    
    return -1

def get_blackliste() :
    return User.query.filter_by(blackliste = True).all()

def get_user(num_tel) :
    return User.query.get(num_tel)

def get_commandes_today() :
    #today = datetime.today().date()
    today = datetime(2024, 11, 6, 12)
    #return Commandes.query.filter(db.func.date(Commandes.date) == today).all()
    return Commandes.query.all()
    