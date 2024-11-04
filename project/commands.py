import click
from .app import app, db

@app.cli.command()#ajoute une commande
@click.argument('filename')#ajoute un argument
def loaddb(filename):
    '''Creates the tables and populates them with data.'''

    # création de toutes les tables
    db.create_all()

    #TODO : Not implemented yet

@app.cli.command ()
def syncdb ():
    """Creates all missing tables. """
    db.create_all()

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