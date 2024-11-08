from project import app, db
from flask import render_template, url_for, redirect, request
#from .models import
from flask_wtf import FlaskForm
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from project.models import Commandes, User, get_sur_place_today

@app.route("/admin")
def admin():
    commandes_sur_place = get_sur_place_today()
    dico_tables = {i: False for i in range(1, 13)}
    for table in commandes_sur_place :
        dico_tables[table.sur_place] = True
    return render_template("admin_traiteur.html", tables = dico_tables)

@app.route("/suivi/commande")
def suivi_commande() :
    return render_template("suivi_commandes.html")

@app.route("/suivi/stock")
def suivi_stock() :
    return render_template("suivi_stock.html")

@app.route("/creation/plat")
def creation_plat():
    return render_template("creation_plat.html")

@app.route("/creation/offre")
def creation_offre():
    return render_template("creation_offre.html")

@app.route("/edition/plat")
def edition_plat():
    return render_template("edition_plat.html")

@app.route("/edition/offre")
def edition_offre():
    return render_template("edition_offre.html")