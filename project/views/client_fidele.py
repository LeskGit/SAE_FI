from ..app import app, db
from flask import render_template, url_for, redirect, request
#from .models import
from flask_wtf import FlaskForm
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256

@app.route("/client/profil")
def client_profil():
    f = ...
    return render_template("profil_client_connecte.html", form=f)

@app.route("/client/historique")
def client_historique():
    return render_template("historique_commandes.html")

@app.route("/client/fidelite")
def client_fidelite():
    return render_template("fidelite_client.html")

@app.route("/client/modif")
def client_modif():
    return render_template("modif_commande.html")