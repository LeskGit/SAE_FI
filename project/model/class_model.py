from flask import flash
from sqlalchemy import CheckConstraint, text
from sqlalchemy.orm import validates
from project.app import MIN_MAX_MODIF, db, login_manager
from flask_login import UserMixin
import re
from datetime import date, datetime, timedelta
from hashlib import sha256
from enum import Enum

client_reductions = db.Table("client_reductions",
    db.Column("id_client", db.Integer, db.ForeignKey("user.id_client"), primary_key=True),
    db.Column("id_reduction", db.Integer, db.ForeignKey("reduction.id_reduction"), primary_key=True)
)

class UserType(Enum):
    USER = 1
    GUEST = 2
    UNKNOW = 3


class User(db.Model, UserMixin):
    id_client = db.Column(db.Integer, primary_key=True, autoincrement=True)
    num_tel = db.Column(
        db.String(10),
        CheckConstraint("LENGTH(num_tel) = 10 AND num_tel REGEXP '^[0-9]+$'"),
        unique=True)
    nom = db.Column(db.String(32))
    prenom = db.Column(db.String(32))
    mdp = db.Column(db.String(64))
    adresse = db.Column(db.String(64))
    email = db.Column(db.String(64), unique=True)
    blackliste = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    points_fidelite = db.Column(db.Integer, default=0)
    fake = db.Column(db.Boolean, default=False)
    les_commandes = db.relationship("Commandes", back_populates="les_clients")
    reductions = db.relationship("Reduction", secondary=client_reductions, back_populates="clients")

    @validates("email")
    def validate_email(self, key, address):
        if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+.[A-Z|a-z]{2,}$",
                        address):
            raise ValueError("Invalid email address")
        return address

    def get_id(self):
        return self.id_client

    def get_num_tel(self):
        return self.num_tel

    def get_panier(self):
        panier = Commandes.query.filter_by(id_client=self.id_client,
                                           etat="Panier").first()
        return panier

    def get_or_create_panier(self):
        panier = self.get_panier()
        if panier is None:
            panier = Commandes(id_client=self.id_client, etat="Panier")
            db.session.add(panier)
            db.session.commit()
        return panier

    def get_nb_items_panier(self):
        panier = self.get_panier()
        if panier is not None:
            return len(panier.constituer_assoc) + len(panier.constituer_formule_assoc)
        return 0

    @classmethod
    def get_blackliste(cls):
        """getter de la blackliste

        Returns:
            list: liste des personnes blacklistés
        """
        return cls.query.filter_by(blackliste=True).all()

    @classmethod
    def get_user(cls, num_tel):
        """getter en fonction du num de téléphone
        """
        return cls.query.filter_by(num_tel=num_tel).first()

    @classmethod
    def check_user_email(cls, email_u):
        """getter en fonction de l'email
        """
        return cls.query.filter_by(email=email_u).first()


@login_manager.user_loader
def load_user(num_tel):
    return User.query.get(num_tel)


CONTENIR_ID_PLAT = "plats.id_plat"

contenir = db.Table(
    "contenir", db.metadata,
    db.Column("id_plat",
              db.Integer,
              db.ForeignKey(CONTENIR_ID_PLAT),
              primary_key=True),
    db.Column("id_formule",
              db.Integer,
              db.ForeignKey("formule.id_formule"),
              primary_key=True))


class Constituer(db.Model):
    __tablename__ = "constituer"
    id_plat = db.Column(db.Integer,
                        db.ForeignKey(CONTENIR_ID_PLAT),
                        primary_key=True)
    num_commande = db.Column(db.Integer,
                             db.ForeignKey("commandes.num_commande"),
                             primary_key=True)
    quantite_plat = db.Column(db.Integer, default=1)
    plat = db.relationship("Plats",
                           back_populates="constituer_assoc",
                           overlaps="les_commandes,commande")
    commande = db.relationship("Commandes",
                               back_populates="constituer_assoc",
                               overlaps="les_plats,plat")

    @classmethod
    def get_constituer(cls, id_plat, num_com):
        """getter de constituer en fonction d'un nom de plat et d'un numéro de commande
        """
        return cls.query.get((id_plat, num_com))
      
class ConstituerFormule(db.Model):
    __tablename__ = "constituer_formule"
    id_formule = db.Column(db.Integer, db.ForeignKey("formule.id_formule"), primary_key=True)
    num_commande = db.Column(db.Integer, db.ForeignKey("commandes.num_commande"), primary_key=True)
    quantite_formule = db.Column(db.Integer, default=1)
    formule = db.relationship("Formule", back_populates="constituer_assoc", overlaps="constituer_assoc,les_commandes")
    commande = db.relationship("Commandes", back_populates="constituer_formule_assoc", overlaps="constituer_formule_assoc,les_formules")

    @classmethod
    def get_constituer(cls, id_formule, num_com):
        return cls.query.get((id_formule, num_com))

class Commandes(db.Model):
    __tablename__ = "commandes"
    num_commande = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_client = db.Column(db.Integer, db.ForeignKey("user.id_client"))
    date = db.Column(db.DateTime)
    date_creation = db.Column(db.DateTime, default=db.func.current_timestamp())
    sur_place = db.Column(db.Boolean, default=False)
    num_table = db.Column(db.Integer, CheckConstraint("0 < num_table AND num_table <= 12"))
    etat = db.Column(db.Enum("Panier", "Non payée", "Payée"), default="Panier")
    les_clients = db.relationship("User", back_populates="les_commandes")
    les_plats = db.relationship("Plats", secondary="constituer", back_populates="les_commandes", overlaps="constituer_assoc,commande,plat")
    constituer_assoc = db.relationship("Constituer", back_populates="commande", overlaps="les_plats,plat")
    les_formules = db.relationship("Formule", secondary="constituer_formule", back_populates="les_commandes", overlaps="constituer_formule_assoc,commande,formule")
    constituer_formule_assoc = db.relationship("ConstituerFormule", back_populates="commande", overlaps="les_formules,commande")
    reductions_ids = set()

    prix_total = 0
    prix_avec_reduc = 0

    def __repr__(self):
        return f"{self.num_commande} : {self.date}"

    def calculer_prix(self):
        self.prix_total = sum([constituer.plat.prix * constituer.quantite_plat for constituer in self.constituer_assoc]) + sum([constituerF.formule.prix * constituerF.quantite_formule for constituerF in self.constituer_formule_assoc])
        return self.prix_total

    def compute_reduction(self, user):
        """
        Calcule le total des remises à appliquer en fonction de deux critères :
        
        1. Si pour un plat commandé, la quantité est supérieure ou égale à la quantité promotionnelle, 
        une réduction fixe (plat.prix_reduc) est appliquée une seule fois.
        
        2. Si l'utilisateur a acheté une réduction pour un plat (via la table Reduction), 
        celle-ci est appliquée en pourcentage sur le prix du plat (une seule fois).
        
        Le montant total de la réduction est renvoyé sous forme négative.
        
        Args:
            user (User): l'utilisateur connecté.
            
        Returns:
            float: le montant total de la réduction (valeur négative).
        """
        total_reduc = 0
        for constituer in self.constituer_assoc:
            plat = constituer.plat
            if constituer.quantite_plat >= plat.quantite_promo:
                total_reduc -= plat.prix_reduc

        reductions_dispo = {reduction.id_plat: reduction for reduction in user.reductions}
        for constituer in self.constituer_assoc:
            plat = constituer.plat
            if plat.id_plat in reductions_dispo:
                reduction_obj = reductions_dispo[plat.id_plat]
                discount = - plat.prix * (reduction_obj.reduction / 100)
                total_reduc += discount

        self.prix_avec_reduc = total_reduc
        return self.prix_avec_reduc


    @classmethod
    def get_num_table_dispo(cls, commande_date: datetime):
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
        return cls.query.filter(
            db.func.date(cls.date) == date, cls.sur_place.is_(True)).all()

    @classmethod
    def get_commandes_today(cls):
        """retourne les commandes d'aujourd'hui
        """
        #today = datetime.today().date()
        #today = datetime(2024, 11, 6, 12)
        #return Commandes.query.filter(db.func.date(Commandes.date) == today).all()
        return cls.query.all()

    @classmethod
    def get_historique(cls, id_client):
        """retourne l'historique de l'User en fonction de son numéro de téléphone

        Args:
            num_tel (str): le numéro de téléphone

        Returns:
            list: la liste des commandes de l'User
        """
        return cls.query.filter_by(id_client=id_client).filter(
            cls.etat != "Panier").order_by(cls.num_commande.desc()).all()

    @classmethod
    def get_commande(cls, num_com):
        """getter en fonction du numéro de commande
        """
        return cls.query.get(num_com)
    
    @classmethod
    def can_modify_commande(cls, id_commande, id_client):
        commande = cls.get_commande(id_commande)
        if commande is None:
            flash("Commande introuvable", "danger")
            return False
        if commande.id_client != id_client:
            flash("Vous n'êtes pas autorisé à modifier cette commande", "danger")
            return False

        now = datetime.now()
        if commande.etat != "Payée":
            elapsed = now - commande.date_creation
            if elapsed >= timedelta(minutes=MIN_MAX_MODIF):
                flash("Vous ne pouvez plus modifier cette commande", "danger")
                return False
        return True


class Allergenes(db.Model):
    id_allergene = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom_allergene = db.Column(db.String(64), unique=True)
    les_plats = db.relationship("Plats",
                                secondary="contenir_allergene",
                                back_populates="les_allergenes")

    @classmethod
    def get_allergenes(cls):
        """getter de tous les allergènes
        """
        return cls.query.order_by(cls.id_allergene).all()


contenir_allergene = db.Table(
    "contenir_allergene", db.metadata,
    db.Column("id_plat",
              db.Integer,
              db.ForeignKey(CONTENIR_ID_PLAT),
              primary_key=True),
    db.Column("id_allergene",
              db.Integer,
              db.ForeignKey("allergenes.id_allergene"),
              primary_key=True))


class Plats(db.Model):
    id_plat = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom_plat = db.Column(db.String(64), unique=True)
    type_plat = db.Column(
        db.Enum("Plat chaud", "Plat froid", "Sushi", "Dessert"))
    stock_utilisable = db.Column(db.Integer)
    stock_reserve = db.Column(db.Integer)
    quantite_defaut = db.Column(db.Integer)
    prix = db.Column(db.Float)
    quantite_promo = db.Column(db.Integer)
    prix_reduc = db.Column(db.Float)
    est_bento = db.Column(db.Boolean, default=False)
    img = db.Column(db.String(200))
    les_allergenes = db.relationship("Allergenes",
                                     secondary="contenir_allergene",
                                     back_populates="les_plats")
    les_formules = db.relationship("Formule",
                                   secondary=contenir,
                                   back_populates="les_plats")

    les_commandes = db.relationship("Commandes",
                                    secondary='constituer',
                                    back_populates="les_plats",
                                    overlaps="constituer_assoc,commande")
    constituer_assoc = db.relationship("Constituer",
                                       back_populates="plat",
                                       overlaps="les_commandes,commande")

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
        return cls.query.filter_by(type_plat="Dessert").all()

    @classmethod
    def get_plats_chauds(cls):
        """getter de tous les plats chauds
        """
        return cls.query.filter_by(type_plat="Plat chaud").all()

    @classmethod
    def get_plats_froids(cls):
        """getter de tous les plats froids
        """
        return cls.query.filter_by(type_plat="Plat froid").all()

    @classmethod
    def get_sushis(cls):
        """getter de tous les sushis
        """
        return cls.query.filter_by(type_plat="Sushi").all()

    @classmethod
    def get_allergenes_plat(cls, nom_plat):
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
            if any(allergene.id_allergene in selected_allergenes
                   for allergene in plat.les_allergenes):
                return True
        return False

    @classmethod
    def get_plats_filtered_by_allergenes(cls, selected_allergenes):
        """getter des plats en fonction d'une liste d'allergènes
        """
        if len(selected_allergenes) == 0:
            return cls.get_plats()
        lst = cls.get_plats()
        for plats in cls.get_plats():
            for allergene in plats.les_allergenes:
                if allergene.id_allergene in selected_allergenes:
                    lst.remove(plats)
                    break
        return lst

    @classmethod
    def get_plats_filtered_by_type_and_allergenes(cls, type_plat,
                                                  selected_allergenes):
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
            if not cls.contains_selected_allergenes(formule,
                                                    selected_allergenes):
                filtered_formules.append(formule)
        return filtered_formules

class Formule(db.Model):
    __tablename__ = "formule"
    id_formule = db.Column(db.Integer, primary_key=True)
    libelle_formule = db.Column(db.String(64))
    prix = db.Column(db.Float)
    les_commandes = db.relationship("Commandes", secondary="constituer_formule", back_populates="les_formules", overlaps="constituer_formule_assoc,commande")
    les_plats = db.relationship("Plats", secondary=contenir, back_populates="les_formules")
    constituer_assoc = db.relationship("ConstituerFormule", back_populates="formule", overlaps="les_commandes,les_formules")

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
  
    @classmethod
    def get_stock_utilisable(cls):
        """getter du stock utilisable du plat avec le moins de quantité
        """
        return min([plat.stock_utilisable for plat in Plats.query.join(contenir).filter(contenir.c.id_formule == cls.id_formule).all()])

class Reduction(db.Model):
    id_reduction = db.Column(db.Integer, primary_key = True)
    id_plat = db.Column(db.Integer, db.ForeignKey(CONTENIR_ID_PLAT))
    reduction = db.Column(db.Integer) # en pourcentage
    points_fidelite = db.Column(db.Integer)
    clients = db.relationship("User", secondary=client_reductions, back_populates="reductions")

    def __repr__(self):
        return f"{self.id_reduction} : {self.reduction}"

    @classmethod
    def get_prix(cls, id_reduction):
        """Calcule le prix du plat après application de la réduction en pourcentage.
        
        Args:
            id_reduction (int): L'identifiant de la réduction.
        
        Returns:
            float: Le prix final du plat après réduction.
        """
        reduc = cls.query.get(id_reduction)
        plat = Plats.query.get(reduc.id_plat)
        prix_initial = plat.prix
        pourcentage = reduc.reduction
        prix_final = prix_initial * (1 - pourcentage / 100)
        return prix_final
    
    @classmethod
    def remove_reduction_association(cls, reduction_id: int, client_id: int) -> None:
        """
        Supprime l'association entre une réduction et un client, par exemple lorsque la réduction a été utilisée.
        
        Args:
            reduction_id (int): l'identifiant de la réduction.
            client_id (int): l'identifiant du client.
        """
        reduction = cls.query.get(reduction_id)
        client = User.query.get(client_id)
        
        if reduction is None:
            raise ValueError("La réduction spécifiée n'existe pas.")
        if client is None:
            raise ValueError("Le client spécifié n'existe pas.")
        
        if client in reduction.clients:
            reduction.clients.remove(client)
            db.session.commit()