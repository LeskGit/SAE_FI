from project import app, db
from flask import render_template, url_for, redirect, request
#from .models import
from flask_wtf import FlaskForm
from wtforms import HiddenField, IntegerField
from wtforms.validators import DataRequired
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from project.models import get_desserts, get_plats, get_formules, Commandes, Constituer

class CommanderForm(FlaskForm) :
    nom_plat = HiddenField()
    num_com = HiddenField()
    quantite = IntegerField(validators=[DataRequired()])

@app.route("/commander")
def commander() :
    if current_user :
        commande = Commandes(num_tel = current_user.num_tel)
        db.session.add(commande)
        db.session.commit()
        num_commande = commande.num_commande
        print(num_commande)
        form = CommanderForm()
        type = request.args.get('type', 'p')
        plats=get_plats()
        formules=get_formules()
        desserts=get_desserts()
        return render_template("commander.html",plats=plats, formules=formules , desserts=desserts, type=type, nb_plats=len(plats), nb_formules=len(formules), nb_desserts=len(desserts), form = form, num_com = num_commande)

@app.route("/commander_plat", methods = ("POST",))
def ajout_plat() :
    if current_user :
        f = CommanderForm()
        if f.num_com.data :
            commande = Commandes.query.get(f.num_com.data)
            constituer = Constituer(nom_plat = f.nom_plat.data, num_commande = f.num_com.data, quantite_plat = f.quantite.data)
            db.session.add(constituer)
            db.session.commit()
            commande.constituer_assoc.append(constituer)

    type = request.args.get('type', 'p')
    plats=get_plats()
    formules=get_formules()
    desserts=get_desserts()
    return render_template("commander.html",plats=plats, formules=formules , desserts=desserts, type=type, nb_plats=len(plats), nb_formules=len(formules), nb_desserts=len(desserts), form = f, num_com = f.num_com.data) 

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
