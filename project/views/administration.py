from project import app, db
from flask import render_template, url_for, redirect, request
from project.models import Plats
from flask_wtf import FlaskForm
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from wtforms import StringField, PasswordField, EmailField, HiddenField
from wtforms.validators import DataRequired, EqualTo, Email, Length, Regexp

class PlatForm(FlaskForm):
    nom = StringField("Nom", validators=[DataRequired(), 
                                          Length(max=32)])
    prix = StringField("Prix", validators=[DataRequired(), 
                                                   Length(max=32)])

@app.route("/admin")
def admin():
    return render_template("admin_traiteur.html")

@app.route("/suivi/commande")
def suivi_commande() :
    return render_template(
        "suivi_commandes.html",
        )

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
    return render_template(
        "edition_plat.html",
        plats=Plats.get_all_plats(Plats)
        )
    
@app.route("/update_plat/<string:id>", methods=["POST"])
def update_plat(id):
    # Récupération des données du formulaire
    nom_plat = request.form.get("nom_plat")
    prix = request.form.get("prix")

    # Validation des données
    if not nom_plat or not prix:
        return "Erreur : Les champs nom_plat et prix sont requis.", 400

    try:
        prix = float(prix)  # Conversion en float
    except ValueError:
        return "Erreur : Le prix doit être un nombre valide.", 400

    # Récupérer le plat par son ID
    plat = db.session.query(Plats).filter_by(nom_plat=id).first()
    if not plat:
        return f"Erreur : Le plat '{id}' n'existe pas.", 404

    # Mise à jour des informations
    plat.nom_plat = nom_plat
    plat.prix = prix
    db.session.commit()

    # Retourner la liste mise à jour des plats
    return render_template(
        "edition_plat.html",
        plats=Plats.query.all()  # Récupérer tous les plats de la base
    )
    
@app.route("/delete_plat/<string:id>", methods=["POST"])
def delete_plat(id):
    # Récupérer le plat par son ID
    plat = db.session.query(Plats).filter_by(nom_plat=id).first()
    if not plat:
        return f"Erreur : Le plat '{id}' n'existe pas.", 404

    # Supprimer le plat
    db.session.delete(plat)
    db.session.commit()

    # Retourner la liste mise à jour des plats
    return render_template(
        "edition_plat.html",
        plats=Plats.query.all()  # Récupérer tous les plats de la base
    )



@app.route("/edition/offre")
def edition_offre():
    return render_template("edition_offre.html")