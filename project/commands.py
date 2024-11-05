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

@app.cli.command()
@click.argument ("username")
@click.argument ("password")
def newuser (username , password ):
    """Adds a new user. """
    from.models import User
    from hashlib import sha256
    m = sha256 ()
    m.update( password.encode())
    u = User( username =username , password =m.hexdigest ())
    db.session.add(u)
    db.session.commit()

@app.cli.command()
@click.argument ("username")
@click.argument ("password")
def newpassword (username, password ):
    """ Change the actual user password. """
    from.models import User
    from hashlib import sha256
    m = sha256 ()
    m.update( password.encode())
    u = User.query.get(username)
    u.password = m.hexdigest ()
    db.session.commit()