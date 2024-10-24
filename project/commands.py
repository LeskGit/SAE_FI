import click
from .app import app, db

@app.cli.command()
def syncdb():
    '''Creates the tables and populates them with data.'''
    db.create_all()

    from .models import TriggerManager, User
    TriggerManager()

    #usr = User(num_tel = '0123456789',
    #            nom = 'Doe',
    #            prenom = 'John',
    #            password = 'password',
    #            adresse = '1 rue de la Paix',
    #            email = 'a@b.c',
    #            blacklisted = False,
    #            points_fidelite = 0,
    #            prix_panier = 0)
    
    #db.session.add(usr)
    #db.session.commit()

    #TODO : Not implemented yet

@app.cli.command()
def dropdb():
    '''Drops the tables.'''

    db.drop_all()
