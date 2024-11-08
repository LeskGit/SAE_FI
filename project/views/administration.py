from project import app, db
from flask import render_template, url_for, redirect, request
#from .models import
from flask_wtf import FlaskForm
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from project.models import get_desserts, get_plats_chauds, get_plats_froids, get_sushis, Plats

@app.route("/admin")
def admin():
    return render_template("admin_traiteur.html")

@app.route("/suivi/commande")
def suivi_commande() :
    return render_template("suivi_commandes.html")

@app.route("/suivi/stock")
def suivi_stock() :
    plats_chauds=get_plats_chauds()
    plats_froids=get_plats_froids()
    sushis=get_sushis()
    desserts=get_desserts()
    return render_template("suivi_stock.html",plats_froids=plats_froids, plats_chauds=plats_chauds, sushis=sushis, desserts=desserts )

@app.route("/modifier_stock", methods=["POST"])
def modifier_stock():
    for key, value in request.form.items():
        nom_plat = key  
        nouveau_stock = int(value)            
        plat = db.session.query(Plats).filter_by(nom_plat=nom_plat).one()
        plat.quantite_stock = nouveau_stock
        db.session.commit()
    
    return redirect(url_for("suivi_stock"))


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