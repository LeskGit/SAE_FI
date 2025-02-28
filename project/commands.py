"""
Modules importés:
    - hashlib: Pour utiliser la fonction de hachage SHA256.
    - click: Pour créer des commandes CLI avec Flask.
    - project.models: Pour importer les modèles de la base de données.
    - .app: Pour importer l'application Flask et la base de données depuis le module app.
    - .models: Pour importer TriggerManager et execute_tests depuis le module models.

Imports:
    - sha256: Fonction de hachage pour sécuriser les mots de passe.
    - click: Module pour créer des commandes CLI personnalisées avec Flask.
    - User: Modèle représentant un utilisateur dans la base de données.
    - app: Instance de l'application Flask.
    - db: Instance de la base de données SQLAlchemy associée à l'application Flask.
    - TriggerManager: Classe pour gérer les triggers dans l'application.
    - execute_tests: Fonction pour exécuter des tests.
"""
from hashlib import sha256
import click
from .model.class_model import User
from .app import app, db
from .model.test_model import execute_tests
from .model.trigger_model import TriggerManager


@app.cli.command()
def syncdb():
    '''Creates the tables and populates them with data.'''

    db.drop_all()

    db.create_all()

    TriggerManager()

    create_admin()

    execute_tests()


@app.cli.command()
def dropdb():
    '''Drops the tables.'''
    db.drop_all()


def create_admin():
    """crée un admin
    """
    password = "admin"
    m = sha256()
    m.update(password.encode())
    hashed_password = m.hexdigest()

    admin = User(
        num_tel="0123456789",
        nom="Admin",
        prenom="Super",
        mdp=hashed_password,
        adresse="123 Rue des Admins",
        email="admin@example.com",
        is_admin=True,
    )

    # Ajout à la base de données
    db.session.add(admin)
    db.session.commit()

    print("Admin créé avec succès !")


@app.cli.command()
@click.argument("num_tel")
def setadmin(num_tel):
    """Set an admin with the given phone number"""
    u = User.query.filter_by(num_tel=num_tel).first()
    if u is None:
        print("User not found")
        return
    u.is_admin = True
    db.session.add(u)
    db.session.commit()