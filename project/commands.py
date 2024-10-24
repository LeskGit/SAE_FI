import click
from .app import app, db

@app.cli.command()
def syncdb():
    '''Creates the tables and populates them with data.'''
    db.create_all()

    #TODO : Not implemented yet

@app.cli.command()
def dropdb():
    '''Drops the tables.'''

    db.drop_all()
