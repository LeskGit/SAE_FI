import click
from .app import app, db

@app.cli.command()
def syncdb():
    '''Creates the tables and populates them with data.'''

    db.drop_all()

    db.create_all()

    from .models import TriggerManager, execute_tests
    TriggerManager()

    #execute_tests()


    #TODO : Not implemented yet

@app.cli.command()
def dropdb():
    '''Drops the tables.'''

    db.drop_all()
