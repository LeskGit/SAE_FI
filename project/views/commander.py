from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from project import app, db
from flask import flash, render_template, url_for, redirect, request
#from .models import
from flask_wtf import FlaskForm
from wtforms import HiddenField, IntegerField
from wtforms.validators import DataRequired
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from project.models import Commandes, Constituer, get_desserts, get_num_table_dispo, get_plats, get_formules, Commandes, Constituer

class CommanderForm(FlaskForm) :
    nom_plat = HiddenField()
    num_com = HiddenField()
    quantite = IntegerField(validators=[DataRequired()])

@app.route("/commander")
def commander() :
    if current_user:
        commande = current_user.get_or_create_panier()
        num_commande = commande.num_commande
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
            try:
                commande = Commandes.query.get(f.num_com.data)
                constituer = Constituer.query.get((f.nom_plat.data, f.num_com.data))
                if constituer:
                    constituer.quantite_plat += f.quantite.data
                else:
                    constituer = Constituer(nom_plat = f.nom_plat.data, num_commande = f.num_com.data, quantite_plat = f.quantite.data)
                    commande.constituer_assoc.append(constituer)
                db.session.add(constituer)
                db.session.commit()
            except Exception as e:
                flash("Erreur : " + str(e._message), "danger")
                return redirect(url_for('commander'))

    return redirect(url_for('commander'))

@app.route("/panier")
def panier():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    panier = current_user.get_or_create_panier()
    if panier is not None:
        panier.calculer_prix()
        panier.compute_reduction()

    if panier.date is None:
        sur_place_disponible = False
    else:
        sur_place_disponible = True if get_num_table_dispo(panier.date) != -1 else False
    return render_template("panier.html", panier=panier, sur_place_disponible=sur_place_disponible)

@app.route('/modifier_quantite')
def modifier_quantite():
    action = request.args.get('action')
    nom_plat = request.args.get('nom_plat')
    if not current_user.is_authenticated:
        panier = None
    else:
        panier = current_user.get_panier()

    if panier is not None:
        for constituer in panier.constituer_assoc:
            if constituer.nom_plat == nom_plat:
                if action == 'increment':
                    if constituer.quantite_plat +1 <= int(constituer.plat.stock_utilisable * 0.8):
                        constituer.quantite_plat += 1
                elif action == 'decrement' and constituer.quantite_plat > 1:
                        constituer.quantite_plat -= 1
                break

        db.session.commit()

    return redirect(url_for('panier'))

@app.route('/modifier_date_heure')
def modifier_date_heure():
    hours = request.args.get('datetime')
    if not current_user.is_authenticated:
        panier = None
    else:
        panier = current_user.get_panier()

    if panier is not None:
        today = datetime.today()
        time = datetime.strptime(hours, "%H:%M").time()
        panier.date = datetime.combine(today, time)
        try:
            db.session.commit()
        except Exception as e:
            flash("Erreur : " + str(e._message), "danger")
            return redirect(url_for('panier'))

    return redirect(url_for('panier'))

@app.route('/modifier_type')
def modifier_type():
    sur_place = request.args.get('delivery')
    if not current_user.is_authenticated:
        panier = None
    else:
        panier = current_user.get_panier()

    if panier is not None:
        if sur_place == "1":
            numero_table = get_num_table_dispo(panier.date)
            if numero_table != -1:
                if panier.date is not None and panier.date.time() > datetime.strptime("14:00", "%H:%M").time():
                    panier.date = datetime.combine(panier.date, datetime.strptime("13:50", "%H:%M").time())
                panier.sur_place = True
                panier.num_table = numero_table
            else:
                panier.sur_place = False 
                panier.num_table = None
        else:
            panier.sur_place = False
            panier.num_table = None
            
        try:
            db.session.commit()
        except Exception as e:
            flash("Erreur : " + str(e._message), "danger")
            return redirect(url_for('panier'))


    return redirect(url_for('panier'))


@app.route('/supprimer_plat')
def supprimer_plat():
    nom_plat = request.args.get('nom_plat')
    if not current_user.is_authenticated:
        panier = None
    else:
        panier = current_user.get_panier()

    for constituer in panier.constituer_assoc:
        if constituer.nom_plat == nom_plat:
            db.session.delete(constituer)

    db.session.commit()

    return redirect(url_for('panier'))

@app.route("/choix_paiement")
def choix_paiement():
    return render_template("choix_paiement.html")

@app.route("/paiement")
def paiement_cb():
    # com1 = Commandes(num_tel = '0123456789',
    #                 date = datetime(2024, 12, 18, 12),
    #                 date_creation = datetime(2024, 11, 6),
    #                 sur_place = False,
    #                 num_table = None,
    #                 etat = "Panier")
    # db.session.add(com1)

    # com1.constituer_assoc.append(Constituer(nom_plat="plat1", num_commande=com1.num_commande, quantite_plat = 3))
    # com1.constituer_assoc.append(Constituer(nom_plat="plat2", num_commande=com1.num_commande, quantite_plat = 3))
    # db.session.commit()
    f = ...
    return render_template("paiement_cb.html", form=f)

@app.route("/paiement/validation", methods = ["POST"])
def validation_paiement():
    if not current_user.is_authenticated:
        panier = None
    else:
        panier = current_user.get_panier()

    if panier is None:
        return redirect(url_for('panier'))

    try:
        panier.etat = "Non payée"
        panier.date_creation = datetime.now()

        for constituer_plat in panier.constituer_assoc:
            constituer_plat.plat.stock_utilisable -= constituer_plat.quantite_plat

        db.session.commit()

    except Exception as e:
        flash("Erreur : " + str(e._message), "danger")
        return redirect(url_for('panier'))




    return render_template("validation_commande.html", panier=panier)