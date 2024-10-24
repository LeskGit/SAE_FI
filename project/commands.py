import click
from .app import app, db

@app.cli.command()#ajoute une commande
@click.argument('filename')#ajoute un argument
def loaddb(filename):
    '''Creates the tables and populates them with data.'''

    # création de toutes les tables
    db.create_all()

    #TODO : Not implemented yet