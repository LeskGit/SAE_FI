from .class_model import User, Constituer, Commandes, Allergenes, Plats, Formule, Reduction
from hashlib import sha256
from ..app import db
from datetime import datetime

def create_allergenes():
    allergene1 = Allergenes(id_allergene=1, nom_allergene='allergene1')
    allergene2 = Allergenes(id_allergene=2, nom_allergene='allergene2')
    allergene3 = Allergenes(id_allergene=3, nom_allergene='allergene3')
    allergene4 = Allergenes(id_allergene=4, nom_allergene='allergene4')
    allergene5 = Allergenes(id_allergene=5, nom_allergene='allergene5')
    allergene6 = Allergenes(id_allergene=6, nom_allergene='allergene6')
    allergene7 = Allergenes(id_allergene=7, nom_allergene='allergene7')
    allergene8 = Allergenes(id_allergene=8, nom_allergene='allergene8')
    allergene9 = Allergenes(id_allergene=9, nom_allergene='allergene9')
    allergene10 = Allergenes(id_allergene=10, nom_allergene='allergene10')

    allergenes = [allergene1, allergene2, allergene3, allergene4, allergene5, allergene6,
        allergene7, allergene8, allergene9, allergene10]
    db.session.add_all(allergenes)
    db.session.commit()
    return allergenes

def execute_tests():
    create_allergenes()
