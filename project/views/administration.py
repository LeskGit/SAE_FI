from project import app, db
from flask import render_template, url_for, redirect, request
#from .models import
from flask_wtf import FlaskForm
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from project.models import Commandes, User, get_sur_place_today, get_blackliste, get_user

@app.route("/admin")
def admin():
    # Tables disponibles aujourd'hui
    commandes_sur_place = get_sur_place_today()
    dico_tables = {i: False for i in range(1, 13)}
    for table in commandes_sur_place :
        dico_tables[table.sur_place] = True
    
    # Blacklist
    liste_noire = get_blackliste()
    return render_template("admin_traiteur.html", tables = dico_tables, blacklist = liste_noire)

@app.route("/admin/blacklist", methods = ["GET", "POST"])
def blackliste_supprimer() :
    user = get_user(request.args.get('id_client'))
    user.blackliste =  False
    db.session.commit()
    return admin()

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