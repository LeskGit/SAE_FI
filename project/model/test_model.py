from .class_model import User, Constituer, Commandes, Allergenes, Plats, Formule
from hashlib import sha256
from ..app import db
from datetime import datetime

def execute_tests():
    password = "password"
    m = sha256()
    m.update(password.encode())
    hashed_password = m.hexdigest()

    usr = User(num_tel='0123456759',
               nom='Doe',
               prenom='John',
               mdp=hashed_password,
               adresse='1 rue de la Paix',
               email='a@b.com',
               blackliste=False,
               points_fidelite=0)

    db.session.add(usr)
    db.session.commit()

    #Allergenes

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

    db.session.add_all([
        allergene1, allergene2, allergene3, allergene4, allergene5, allergene6,
        allergene7, allergene8, allergene9, allergene10
    ])
    db.session.commit()

    #5 Plats
    plat1 = Plats(nom_plat='plat1',
                  type_plat='Plat chaud',
                  stock_utilisable=10,
                  quantite_defaut=7,
                  prix=10,
                  quantite_promo=2,
                  prix_reduc=10,
                  img='sushi.jpg')

    plat2 = Plats(nom_plat='plat2',
                  type_plat='Plat froid',
                  stock_utilisable=10,
                  quantite_defaut=6,
                  prix=10,
                  quantite_promo=0,
                  prix_reduc=0,
                  img='sushi.jpg')

    plat3 = Plats(nom_plat='plat3',
                  type_plat='Sushi',
                  stock_utilisable=10,
                  quantite_defaut=8,
                  prix=10,
                  quantite_promo=0,
                  prix_reduc=0,
                  img='sushi.jpg')

    plat4 = Plats(nom_plat='plat4',
                  type_plat='Dessert',
                  stock_utilisable=10,
                  quantite_defaut=12,
                  prix=10,
                  quantite_promo=0,
                  prix_reduc=0,
                  img='sushi.jpg')

    plat5 = Plats(nom_plat='plat5',
                  type_plat='Plat chaud',
                  stock_utilisable=10,
                  quantite_defaut=7,
                  prix=10,
                  quantite_promo=0,
                  prix_reduc=0,
                  img='sushi.jpg')

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
    formule1 = Formule(id_formule=1, libelle_formule='formule1', prix=20)

    db.session.add(formule1)

    com1 = Commandes(id_client=1,
                     date=datetime(2024, 11, 6, 12),
                     date_creation=datetime(2024, 11, 6),
                     sur_place=True,
                     num_table=1,
                     etat="Payée")

    com2 = Commandes(id_client=1,
                     date=datetime(2024, 11, 5, 12),
                     date_creation=datetime(2024, 11, 1),
                     sur_place=True,
                     num_table=2,
                     etat="Payée")

    com3 = Commandes(id_client=1,
                     date=datetime(2024, 11, 6, 12),
                     date_creation=datetime(2024, 11, 1),
                     sur_place=True,
                     num_table=3,
                     etat="Payée")

    com4 = Commandes(id_client=1,
                     date=datetime(2024, 11, 5, 12),
                     date_creation=datetime(2024, 11, 1),
                     sur_place=True,
                     num_table=4,
                     etat="Payée")

    com5 = Commandes(id_client=1,
                     date=datetime(2024, 11, 6, 12),
                     date_creation=datetime(2024, 11, 1),
                     sur_place=True,
                     num_table=5,
                     etat="Payée")

    com6 = Commandes(id_client=1,
                     date=datetime(2024, 11, 5, 12),
                     date_creation=datetime(2024, 11, 1),
                     sur_place=True,
                     num_table=6,
                     etat="Payée")

    com7 = Commandes(id_client=1,
                     date=datetime(2024, 11, 6, 12),
                     date_creation=datetime(2024, 11, 1),
                     sur_place=False,
                     num_table=None,
                     etat="Payée")

    com8 = Commandes(id_client=1,
                     date=datetime(2024, 11, 5, 12),
                     date_creation=datetime(2024, 11, 1),
                     sur_place=True,
                     num_table=8,
                     etat="Payée")

    com9 = Commandes(id_client=1,
                     date=datetime(2024, 11, 6, 12),
                     date_creation=datetime(2024, 11, 1),
                     sur_place=True,
                     num_table=9,
                     etat="Payée")

    com10 = Commandes(id_client=1,
                      date=datetime(2024, 11, 5, 12),
                      date_creation=datetime(2024, 11, 1),
                      sur_place=True,
                      num_table=10,
                      etat="Payée")

    com11 = Commandes(id_client=1,
                      date=datetime(2024, 11, 6, 12),
                      date_creation=datetime(2024, 11, 1),
                      sur_place=True,
                      num_table=11,
                      etat="Payée")

    com12 = Commandes(id_client=1,
                      date=datetime(2024, 11, 5, 12),
                      date_creation=datetime(2024, 11, 4, 10),
                      sur_place=True,
                      num_table=12,
                      etat="Payée")

    com13 = Commandes(id_client=1,
                      date=datetime(2024, 11, 6, 13),
                      date_creation=datetime(2024, 11, 4, 10),
                      sur_place=True,
                      num_table=12,
                      etat="Non Payée")

    com13 = Commandes(id_client=1,
                      date=datetime(2024, 12, 18, 13),
                      date_creation=datetime(2024, 12, 18, 10, 5),
                      sur_place=False,
                      etat="Panier")

    db.session.add_all([
        com1, com2, com3, com4, com5, com6, com7, com8, com9, com10, com11,
        com12, com13
    ])

    db.session.commit()

    commande = Commandes.query.get(1)

    try:
        # Ajouter des plats à Constituer pour la commande
        constituer_assoc = [
            Constituer(id_plat=1,
                       num_commande=commande.num_commande,
                       quantite_plat=2),
            Constituer(id_plat=2,
                       num_commande=commande.num_commande,
                       quantite_plat=3),
            Constituer(id_plat=3,
                       num_commande=commande.num_commande,
                       quantite_plat=1)
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
