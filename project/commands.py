import click
from .app import app, db
from project.models import User
from hashlib import sha256

@app.cli.command()
def syncdb():
    '''Creates the tables and populates them with data.'''

    db.drop_all()

    db.create_all()

    from .models import TriggerManager, execute_tests
    TriggerManager()

    create_admin()

    #execute_tests()

@app.cli.command()
def dropdb():
    '''Drops the tables.'''

    db.drop_all()

def create_admin():
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