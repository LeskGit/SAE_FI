from project import app, db
from flask import render_template, url_for, redirect, request
#from .models import
from flask_wtf import FlaskForm
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from project.models import get_desserts, get_plats, get_formules

@app.route("/commander")
def commander() :
    type = request.args.get('type', 'p')
    return render_template("commander.html",plats=get_plats(), formules=get_formules(), desserts=get_desserts(), type=type)

@app.route("/commander_plat", methods = ("POST",))
def ajout_plat() :
    ...

@app.route("/panier")
def panier() :
    return render_template("panier.html")

@app.route("/choix_paiement")
def choix_paiement() :
    return render_template("choix_paiement.html")

@app.route("/paiement")
def paiement_cb():
    f = ...
    return render_template("paiement_cb.html", form=f)
