"""
Ce module initialise les différentes vues et commandes 
de l'application ainsi que la base de données.
"""
from .app import app, db
import project.views.administration
import project.views.authentification
import project.views.client_fidele
import project.views.commander
import project.views.home_views
import project.commands
import project.models
