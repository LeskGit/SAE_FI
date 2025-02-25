from sqlalchemy import CheckConstraint, text
from sqlalchemy.orm import validates
from .app import db, login_manager
from flask_login import UserMixin
import re
from datetime import date, datetime, timedelta
from hashlib import sha256
from enum import Enum

class UserType(Enum):
    USER = 1
    GUEST = 2
    UNKNOW = 3

class User(db.Model, UserMixin):
    id_client = db.Column(db.Integer, primary_key = True, autoincrement=True)
    num_tel = db.Column(db.String(10), CheckConstraint("LENGTH(num_tel) = 10 AND num_tel REGEXP '^[0-9]+$'"), unique=True)
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
    fake = db.Column(db.Boolean, default=False)
    les_commandes = db.relationship("Commandes", back_populates = "les_clients")

    @validates("email")
    def validate_email(self, key, address):
        if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+.[A-Z|a-z]{2,}$", address):
            raise ValueError("Invalid email address")
        return address
    
    def get_id(self):
        return self.id_client
    
    def get_num_tel(self):
        return self.num_tel

    def get_panier(self):
        panier = Commandes.query.filter_by(id_client = self.id_client, etat = "Panier").first()
        return panier
    
    def get_or_create_panier(self):
        panier = self.get_panier()
        if panier is None:
            panier = Commandes(id_client = self.id_client, etat="Panier")
            db.session.add(panier)
            db.session.commit()
        return panier
    
    def get_nb_items_panier(self):
        panier = self.get_panier()
        if panier is not None:
            return len(panier.constituer_assoc)
        return 0
    @classmethod
    def get_blackliste(cls) :
        """getter de la blackliste

        Returns:
            list: liste des personnes blacklistés
        """
        return cls.query.filter_by(blackliste = True).all()
    
    @classmethod
    def get_user(cls, num_tel) :
        """getter en fonction du num de téléphone
        """
        return cls.query.filter_by(num_tel=num_tel).first()
    
    @classmethod
    def check_user_email(cls, email_u) :
        """getter en fonction de l'email
        """
        return cls.query.filter_by(email=email_u).first()

@login_manager.user_loader
def load_user(num_tel):
    return User.query.get(num_tel)

CONTENIR_ID_PLAT = "plats.id_plat"

contenir = db.Table("contenir",
    db.metadata,
    db.Column("id_plat", db.Integer, db.ForeignKey(CONTENIR_ID_PLAT), primary_key=True),
    db.Column("id_formule", db.Integer, db.ForeignKey("formule.id_formule"), primary_key=True)
)

class Constituer(db.Model):
    __tablename__ = "constituer"
    id_plat = db.Column(db.Integer, db.ForeignKey(CONTENIR_ID_PLAT), primary_key=True)
    num_commande = db.Column(db.Integer, db.ForeignKey("commandes.num_commande"), primary_key=True)
    quantite_plat = db.Column(db.Integer, default=1)
    plat = db.relationship("Plats", back_populates="constituer_assoc", overlaps="les_commandes,commande")
    commande = db.relationship("Commandes", back_populates="constituer_assoc", overlaps="les_plats,plat")

    @classmethod
    def get_constituer(cls, id_plat, num_com) :
        """getter de constituer en fonction d'un nom de plat et d'un numéro de commande
        """
        return cls.query.get((id_plat, num_com))

class Commandes(db.Model):
    num_commande = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_client = db.Column(db.Integer, db.ForeignKey("user.id_client"))
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
        """Calcule la réduction de la commande :
            Applique le prix - prix_reduc pour chaque plat en promotion (constituer.quantite_plat > quantite_promo)
        """
        self.prix_avec_reduc = 0
        for constituer in self.constituer_assoc:
            if constituer.quantite_plat >= constituer.plat.quantite_promo:
                self.prix_avec_reduc -= constituer.plat.prix_reduc
        return self.prix_avec_reduc
    
    @classmethod
    def get_num_table_dispo(cls, commande_date:datetime):
        """Renvoie le numéro de la première table disponible
        """
        commandes_sur_place = cls.get_sur_place_at(commande_date.date())

        dico_tables = {i: False for i in range(1, 13)}
        for table in commandes_sur_place:
            dico_tables[table.num_table] = True
        
        for num_table, occupe in dico_tables.items():
            if not occupe:
                return num_table
        
        return -1
    
    @classmethod
    def get_sur_place_at(cls, date=datetime.today().date()):
        """Retourne les tables disponibles à la date donnée

        Args:
            date (datetime, optional): la date à vérifier. Par défaut à datetime.today().date().

        Returns:
            list: la liste des tables disponibles à la date donnée
        """
        return cls.query.filter(db.func.date(cls.date) == date, cls.sur_place.is_(True)).all()
    
    @classmethod
    def get_commandes_today(cls) :
        """retourne les commandes d'aujourd'hui
        """
        #today = datetime.today().date()
        #today = datetime(2024, 11, 6, 12)
        #return Commandes.query.filter(db.func.date(Commandes.date) == today).all()
        return cls.query.all()
    
    @classmethod
    def get_historique(cls, id_client) :
        """retourne l'historique de l'User en fonction de son numéro de téléphone

        Args:
            num_tel (str): le numéro de téléphone

        Returns:
            list: la liste des commandes de l'User
        """
        return cls.query.filter_by(id_client=id_client).filter(cls.etat != "Panier").order_by(cls.num_commande.desc()).all()

    @classmethod
    def get_commande(cls, num_com) :
        """getter en fonction du numéro de commande
        """
        return cls.query.get(num_com)
    
class Allergenes(db.Model):
    id_allergene = db.Column(db.Integer, primary_key = True, autoincrement=True)
    nom_allergene = db.Column(db.String(64), unique = True)
    les_plats = db.relationship("Plats", secondary = "contenir_allergene", back_populates = "les_allergenes")

    @classmethod
    def get_allergenes(cls) :
        """getter de tous les allergènes
        """
        return cls.query.order_by(cls.id_allergene).all()
    
contenir_allergene = db.Table("contenir_allergene",
    db.metadata,
    db.Column("id_plat", db.Integer, db.ForeignKey(CONTENIR_ID_PLAT), primary_key=True),
    db.Column("id_allergene", db.Integer, db.ForeignKey("allergenes.id_allergene"), primary_key=True)
)

class Plats(db.Model):
    id_plat = db.Column(db.Integer, primary_key = True, autoincrement=True)
    nom_plat = db.Column(db.String(64), unique = True)
    type_plat = db.Column(db.Enum("Plat chaud", "Plat froid", "Sushi", "Dessert"))
    stock_utilisable = db.Column(db.Integer)
    stock_reserve = db.Column(db.Integer)
    quantite_defaut = db.Column(db.Integer)
    prix = db.Column(db.Float)
    quantite_promo = db.Column(db.Integer)
    prix_reduc = db.Column(db.Float)
    est_bento = db.Column(db.Boolean, default=False)
    img = db.Column(db.String(200))
    les_allergenes = db.relationship("Allergenes", secondary = "contenir_allergene", back_populates = "les_plats")
    les_formules = db.relationship("Formule", secondary = contenir, back_populates="les_plats")
    
    les_commandes = db.relationship("Commandes", secondary = 'constituer', back_populates = "les_plats", overlaps="constituer_assoc,commande")
    constituer_assoc = db.relationship("Constituer", back_populates="plat", overlaps="les_commandes,commande")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.stock_utilisable is not None:
            self.stock_reserve = int(self.stock_utilisable * 0.2)
            
    def add_allergene(self, lst_allergenes):
        for allergene in lst_allergenes:
            self.les_allergenes.append(allergene)

    def __repr__(self):
        return f"{self.nom_plat} ({self.type_plat}) : {self.prix}"
    
    @classmethod
    def get_plats(cls):
        """getter de tous les plats
        """
        return cls.query.all()
    
    @classmethod
    def get_desserts(cls):
        """getter de tous les desserts
        """     
        return cls.query.filter_by(type_plat = "Dessert").all()

    @classmethod
    def get_plats_chauds(cls):
        """getter de tous les plats chauds
        """
        return cls.query.filter_by(type_plat = "Plat chaud").all()

    @classmethod
    def get_plats_froids(cls):
        """getter de tous les plats froids
        """
        return cls.query.filter_by(type_plat = "Plat froid").all()

    @classmethod
    def get_sushis(cls):
        """getter de tous les sushis
        """
        return cls.query.filter_by(type_plat = "Sushi").all()
    
    @classmethod
    def get_allergenes_plat(cls, nom_plat) :
        """getter des allerènes en fonction d'un nom de plat
        """
        return cls.query.get(nom_plat).les_allergenes

    def contains_selected_allergenes(formule, selected_allergenes):
        """Fonction vérifiant si un ou plusieurs allergènes est/sont dans une formule

        Args:
            formule (Formule): la formule
            selected_allergenes (List(Allergene)): la liste des allergènes à vérifier

        Returns:
            boolean: Vrai si au moins un allergène est dans la formule
        """
        for plat in formule.les_plats:
            if any(allergene.id_allergene in selected_allergenes for allergene in plat.les_allergenes):
                return True
        return False

    @classmethod
    def get_plats_filtered_by_allergenes(cls, selected_allergenes):
        """getter des plats en fonction d'une liste d'allergènes
        """
        if len(selected_allergenes) == 0:
            return cls.get_plats()  
        else:
            lst = cls.get_plats()
            for plats in cls.get_plats():
                for allergene in plats.les_allergenes:
                    if allergene.id_allergene in selected_allergenes:
                        lst.remove(plats)
                        break
            return lst

    @classmethod
    def get_plats_filtered_by_type_and_allergenes(cls, type_plat, selected_allergenes):
        """getter des plats en fonction de leur type et d'une liste d'allergènes
        """
        res = []
        plat_trie = cls.get_plats_filtered_by_allergenes(selected_allergenes)
        for plats in plat_trie:
            if plats.type_plat == type_plat:
                res.append(plats)
        return res

    @classmethod
    def filter_formules_by_allergenes(cls, formules, selected_allergenes):
        """Fonction permettant de récupérer les formules filtrées par une liste d'allergènes

        Args:
            formules (List(Formule)): la liste de formules
            selected_allergenes (List(Allergene)): la liste des allergènes

        Returns:
            List(Formule): la liste des formules filtrées
        """
        filtered_formules = []
        for formule in formules:
            if not cls.contains_selected_allergenes(formule, selected_allergenes):
                filtered_formules.append(formule)
        return filtered_formules

class Formule(db.Model):
    id_formule = db.Column(db.Integer, primary_key = True)
    libelle_formule = db.Column(db.String(64))
    prix = db.Column(db.Float)
    les_plats = db.relationship("Plats", secondary = contenir, back_populates = "les_formules")

    def __repr__(self):
        return f"{self.id_formule} : {self.libelle_formule}"
    
    @classmethod
    def get_formules(cls):
        """getter des formules
        """
        return cls.query.all()
    
    @classmethod
    def get_formules_filtered_by_allergenes(cls, selected_allergenes):
        """getter des formules en fonction d'une liste d'allergènes
        """
        if len(selected_allergenes) == 0:
            return cls.get_formules()
        else:
            return Plats.filter_formules_by_allergenes(cls.get_formules(), selected_allergenes)

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
            IF (SELECT blackliste FROM user WHERE id_client = NEW.id_client) = 1 THEN
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
            IF (SELECT blackliste FROM user WHERE id_client = NEW.id_client) = 1 THEN
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
            WHERE id_client = NEW.id_client AND etat = 'Non payée';

            IF temps >= 24 THEN
                UPDATE user
                SET blackliste = True
                WHERE id_client = NEW.id_client;
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
            WHERE id_client = NEW.id_client AND etat = 'Non payée';

            IF temps >= 24 THEN
                UPDATE user
                SET blackliste = True
                WHERE id_client = NEW.id_client;
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
            WHERE id_plat = NEW.id_plat;

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
            WHERE id_plat = NEW.id_plat;

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
            WHERE id_plat = NEW.id_plat;

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
            DECLARE n int;

            SELECT count(id_plat) into nombre
            FROM contenir
            WHERE id_formule = NEW.id_formule;

            IF nombre > 3 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "La formule est déjà complète";
            END IF;

            SELECT type_plat into type
            FROM plats
            WHERE id_plat = NEW.id_plat;

            SELECT id_plat into n
            FROM contenir
            WHERE id_plat in (
            SELECT id_plat
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
            JOIN plats p ON c.id_plat = p.id_plat
            WHERE c.id_formule = NEW.id_formule
            AND p.type_plat = (SELECT type_plat FROM plats WHERE id_plat = NEW.id_plat)
            AND c.id_plat != OLD.id_plat;

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
                WHERE id_client = NEW.id_client and
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

    def trigger_fidelite_insert(self) -> str:
        """
        Permet d'ajouter des points de fidelité à un utilisateur à chaque commande
        """
        return """
        CREATE TRIGGER fidelite_insert AFTER INSERT ON commandes FOR EACH ROW
        BEGIN
            DECLARE user VARCHAR(62);
            DECLARE points INT;

            if NEW.etat = "Payée" THEN
                SELECT id_client into user
                FROM user
                WHERE id_client = NEW.id_client;

                Select points_fidelite into points
                FROM user
                WHERE id_client = user;

                UPDATE user
                SET points_fidelite = points + 10
                WHERE id_client = user;
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
    
    #Allergenes
    
    allergene1 = Allergenes(id_allergene = 1, nom_allergene = 'allergene1')
    allergene2 = Allergenes(id_allergene = 2, nom_allergene = 'allergene2')
    allergene3 = Allergenes(id_allergene = 3, nom_allergene = 'allergene3')
    allergene4 = Allergenes(id_allergene = 4, nom_allergene = 'allergene4')
    allergene5 = Allergenes(id_allergene = 5, nom_allergene = 'allergene5')
    allergene6 = Allergenes(id_allergene = 6, nom_allergene = 'allergene6')
    allergene7 = Allergenes(id_allergene = 7, nom_allergene = 'allergene7')
    allergene8 = Allergenes(id_allergene = 8, nom_allergene = 'allergene8')
    allergene9 = Allergenes(id_allergene = 9, nom_allergene = 'allergene9')
    allergene10 = Allergenes(id_allergene = 10, nom_allergene = 'allergene10')
    
    db.session.add_all([allergene1, allergene2, allergene3, allergene4, allergene5, allergene6, allergene7, allergene8, allergene9, allergene10])
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
                quantite_defaut = 7,
                prix = 10,
                quantite_promo = 0,
                prix_reduc = 0,
                img = 'sushi.jpg')
    
    
    db.session.add_all([plat1, plat2, plat3, plat4, plat5])

    # Ajouter les allergènes aux plats
    plat1.les_allergenes.append(allergene1)
    plat1.les_allergenes.append(allergene2)
    plat2.les_allergenes.append(allergene3)
    plat2.les_allergenes.append(allergene4)
    plat3.les_allergenes.append(allergene5)
    plat3.les_allergenes.append(allergene6)
    plat4.les_allergenes.append(allergene7)
    plat4.les_allergenes.append(allergene8)
    plat5.les_allergenes.append(allergene9)
    plat5.les_allergenes.append(allergene10)
    db.session.commit()
    
    
    #Formule
    formule1 = Formule(id_formule = 1,
                        libelle_formule = 'formule1',
                        prix = 20)
    
    db.session.add(formule1)

    com1 = Commandes(id_client = 1,
                        date = datetime(2024, 11, 6, 12),
                        date_creation = datetime(2024, 11, 6),
                        sur_place = True,
                        num_table = 1,
                        etat = "Payée")

    com2 = Commandes(id_client = 1,
                        date = datetime(2024, 11, 5, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = True,
                        num_table = 2,
                        etat = "Payée")

    com3 = Commandes(id_client = 1,
                        date = datetime(2024, 11, 6, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = True,
                        num_table = 3,
                        etat = "Payée")

    com4 = Commandes(id_client = 1,
                        date = datetime(2024, 11, 5, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = True,
                        num_table = 4,
                        etat = "Payée")

    com5 = Commandes(id_client = 1,
                        date = datetime(2024, 11, 6, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = True,
                        num_table = 5,
                        etat = "Payée")

    com6 = Commandes(id_client = 1,
                        date = datetime(2024, 11, 5, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = True,
                        num_table = 6,
                        etat = "Payée")

    com7 = Commandes(id_client = 1,
                        date = datetime(2024, 11, 6, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = False,
                        num_table = None,
                        etat = "Payée")

    com8 = Commandes(id_client = 1,
                        date = datetime(2024, 11, 5, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = True,
                        num_table = 8,
                        etat = "Payée")

    com9 = Commandes(id_client = 1,
                        date = datetime(2024, 11, 6, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = True,
                        num_table = 9,
                        etat = "Payée")

    com10 = Commandes(id_client = 1,
                        date = datetime(2024, 11, 5, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = True,
                        num_table = 10,
                        etat = "Payée")

    com11 = Commandes(id_client = 1,
                        date = datetime(2024, 11, 6, 12),
                        date_creation = datetime(2024, 11, 1),
                        sur_place = True,
                        num_table = 11,
                        etat = "Payée")

    com12 = Commandes(id_client = 1,
                        date = datetime(2024, 11, 5, 12),
                        date_creation = datetime(2024, 11, 4, 10),
                        sur_place = True,
                        num_table = 12,
                        etat = "Payée")

    com13 = Commandes(id_client = 1,
                        date = datetime(2024, 11, 6, 13),
                        date_creation = datetime(2024, 11, 4, 10),
                        sur_place = True,
                        num_table = 12,
                        etat = "Non Payée")
    
    com13 = Commandes(id_client = 1,
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
            Constituer(id_plat=1, num_commande=commande.num_commande, quantite_plat=2),
            Constituer(id_plat=2, num_commande=commande.num_commande, quantite_plat=3),
            Constituer(id_plat=3, num_commande=commande.num_commande, quantite_plat=1)
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