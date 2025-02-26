from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from project import app, db
from flask import flash, render_template, url_for, redirect, request, make_response, session
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import BooleanField, SubmitField, StringField
from wtforms import HiddenField, IntegerField
from wtforms.validators import DataRequired
from flask_login import login_user, current_user, logout_user, login_required
from hashlib import sha256
from project.models import ConstituerFormule, Plats, Allergenes, Constituer, Commandes, Formule, User, UserType


def get_current_user():
    if current_user.is_authenticated:
        return current_user
    elif session.get('user') is not None:
        user_id = session.get('user')
        return User.get_user(user_id)
    return None


def callback_type_user(callback_user, callback_guest, callback_unknown):
    if current_user.is_authenticated:
        return callback_user()
    elif session.get('user') is not None:
        return callback_guest()
    return callback_unknown()


def get_type_user():
    return callback_type_user(lambda: UserType.USER, lambda: UserType.GUEST,
                              lambda: UserType.UNKNOW)


class CommanderForm(FlaskForm):
    id_plat = HiddenField()
    num_com = HiddenField()
    quantite = IntegerField(validators=[DataRequired()])


def get_plats_type(type, selected_allergenes, query_plats, search_allergenes):
    match type:
        case "pc":
            return Plats.get_plats_filtered_by_type_and_allergenes("Plat chaud", selected_allergenes)
        case "pf":
            return Plats.get_plats_filtered_by_type_and_allergenes("Plat froid", selected_allergenes)
        case "s":
            return Plats.get_plats_filtered_by_type_and_allergenes("Sushi", selected_allergenes)
        case "f":
            return Formule.get_formules_filtered_by_allergenes(selected_allergenes)
        case "d":
            return Plats.get_plats_filtered_by_type_and_allergenes("Dessert", selected_allergenes)
    
    if search_allergenes:
        return Plats.get_plats_filtered_by_allergenes(selected_allergenes)
    return Plats.query.filter(Plats.nom_plat.like(f"%{query_plats}%")).all() if query_plats is not None else Plats.get_plats()
        

@app.route("/commander", methods=["GET", "POST"])
def commander():
    user = get_current_user()
    if user is None:
        return redirect(url_for('login_unsafe'))

    commande = user.get_or_create_panier()
    num_commande = commande.num_commande
    form = CommanderForm()

    allergenes = Allergenes.get_allergenes()
    type = request.args.get('type', 'p')
    selected_allergenes = request.form.getlist('allergenes')  # Liste des allergènes cochés
    query_plats = request.args.get('query', "")
    
    les_plats = get_plats_type(type, selected_allergenes, query_plats, False)

    return render_template("commander.html", 
                        list_plats=les_plats,
                        list_allergenes=allergenes,
                        selected_allergenes=selected_allergenes,
                        type=type,
                        form=form,
                        num_com = num_commande)

@app.route("/filter_allergenes", methods=["GET", "POST"])
def filter_allergenes():

    user = get_current_user()
    if user is None:
        return redirect(url_for('login_unsafe'))

    # Récupérer la liste des allergènes sélectionnés
    if request.method == "POST":
        selected_allergenes = request.form.getlist(
            'allergenes')  # Liste des allergènes cochés

        for i in range(len(selected_allergenes)):
            selected_allergenes[i] = int(selected_allergenes[i])
    if request.method == "GET":
        selected_allergenes = request.cookies.get('allergenes')
        if selected_allergenes:
            selected_allergenes = selected_allergenes.split(',')
            for i in range(len(selected_allergenes)):
                if (selected_allergenes[i] != ""):
                    selected_allergenes[i] = int(selected_allergenes[i])
        else:
            selected_allergenes = []
    commande = user.get_or_create_panier()
    num_commande = commande.num_commande
    form = CommanderForm()

    allergenes = Allergenes.get_allergenes()

    type = request.args.get('type', 'p')
    query_plats = request.args.get('query', "")
    
    les_plats = get_plats_type(type, selected_allergenes, query_plats, True)

    resp = make_response(render_template("commander.html", 
                        list_plats=les_plats,
                        list_allergenes=allergenes,
                        selected_allergenes=selected_allergenes,
                        type=type,
                        form=form,
                        num_com = num_commande))
    
    if request.method == "POST":
        string_allergenes = ""
        for al in selected_allergenes:
            string_allergenes += str(al) + ","
        resp.set_cookie('allergenes', string_allergenes)
    # Rendre la page commander avec les données filtrées
    return resp


@app.route("/commander_plat", methods=("POST",))
def ajout_plat():
    f = CommanderForm()
    if f.num_com.data:
        try:
            commande = Commandes.get_commande(f.num_com.data)
            constituer = Constituer.get_constituer(f.id_plat.data,
                                                   f.num_com.data)
            if constituer:
                constituer.quantite_plat += f.quantite.data
            else:
                constituer = Constituer(id_plat=f.id_plat.data,
                                        num_commande=f.num_com.data,
                                        quantite_plat=f.quantite.data)
                commande.constituer_assoc.append(constituer)
            db.session.add(constituer)
            db.session.commit()
        except Exception as e:
            flash("Erreur : " + str(e.orig.args[1]), "danger")
            return redirect(url_for('commander'))

    return redirect(url_for('commander'))

@app.route("/commander_formule", methods=["POST"])
def ajout_formule():
    if current_user.is_authenticated:
        form = CommanderForm()
        if form.num_com.data:
            try:
                commande = Commandes.get_commande(form.num_com.data)
                constituer_formule = ConstituerFormule.get_constituer(form.id_plat.data, form.num_com.data)
                
                if constituer_formule:
                    constituer_formule.quantite_formule += form.quantite.data
                else:
                    constituer_formule = ConstituerFormule(
                        id_formule=form.id_plat.data, 
                        num_commande=form.num_com.data, 
                        quantite_formule=form.quantite.data
                    )
                    commande.constituer_formule_assoc.append(constituer_formule)

                db.session.add(constituer_formule)
                db.session.commit()
            except Exception as e:
                flash("Erreur : " + str(e), "danger")
                return redirect(url_for('commander'))

    return redirect(url_for('commander'))

@app.route("/panier")
def panier():
    user = get_current_user()
    if user is None:
        return redirect(url_for('login_unsafe'))

    panier = user.get_or_create_panier()
    if panier is not None:
        panier.calculer_prix()
        panier.compute_reduction()

    if panier.date is None:
        sur_place_disponible = False
    else:
        sur_place_disponible = True if Commandes.get_num_table_dispo(
            panier.date) != -1 else False
    return render_template("panier.html",
                           panier=panier,
                           sur_place_disponible=sur_place_disponible)


@app.route('/modifier_quantite')
def modifier_quantite():
    action = request.args.get('action')
    nom_plat = request.args.get('nom_plat')
    user = get_current_user()
    if user is not None:
        panier = user.get_panier()
        if panier is not None:
            for constituer in panier.constituer_assoc:
                if constituer.plat.nom_plat == nom_plat:
                    if action == 'increment':
                        if constituer.quantite_plat + 1 <= int(
                                constituer.plat.stock_utilisable * 0.8):
                            constituer.quantite_plat += 1
                    elif action == 'decrement' and constituer.quantite_plat > 1:
                        constituer.quantite_plat -= 1
                    break
        try : 
            db.session.commit()
        except sqlalchemy.exc.OperationalError as e:
            db.session.rollback()
            flash("Erreur : " + str(e.orig.args[1]), "danger")

        db.session.commit()

    return redirect(url_for('panier'))

@app.route('/modifier_quantite_formule')
def modifier_quantite_formule():
    action = request.args.get('action')
    libelle_formule = request.args.get('libelle_formule')
    user = get_current_user()
    if user is not None:
        panier = user.get_panier()
        if panier is not None:
            for constituer in panier.constituer_formule_assoc:
                if constituer.formule.libelle_formule == libelle_formule:
                    if action == 'increment':
                        if constituer.quantite_formule +1 <= int(constituer.formule.get_stock_utilisable() * 0.8):
                            constituer.quantite_formule += 1
                    elif action == 'decrement' and constituer.quantite_formule > 1:
                        constituer.quantite_formule -= 1
                    break
        try : 
            db.session.commit()
        except sqlalchemy.exc.OperationalError as e:
            db.session.rollback()
            flash("Erreur : " + str(e.orig.args[1]), "danger")

        db.session.commit()

    return redirect(url_for('panier'))

@app.route('/modifier_date_heure')
def modifier_date_heure():
    hours = request.args.get('datetime')

    user = get_current_user()
    if user is not None:
        panier = user.get_panier()
        if panier is not None:
            today = datetime.today()
            time = datetime.strptime(hours, "%H:%M").time()
            panier.date = datetime.combine(today, time)
            try:
                db.session.commit()
            except sqlalchemy.exc.OperationalError as e:
                flash("Erreur : " + str(e.orig.args[1]), "danger")
                return redirect(url_for('panier'))

    return redirect(url_for('panier'))


@app.route('/modifier_type')
def modifier_type():
    sur_place = request.args.get('delivery')

    user = get_current_user()
    if user is not None:
        panier = user.get_panier()
        if panier is not None:
            if sur_place == "1":
                numero_table = Commandes.get_num_table_dispo(panier.date)
                if numero_table != -1:
                    if panier.date is not None and panier.date.time(
                    ) > datetime.strptime("14:00", "%H:%M").time():
                        panier.date = datetime.combine(
                            panier.date,
                            datetime.strptime("13:50", "%H:%M").time())
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
                flash("Erreur : " + str(e), "danger")
                return redirect(url_for('panier'))

    return redirect(url_for('panier'))


@app.route('/supprimer_plat')
def supprimer_plat():
    nom_plat = request.args.get('nom_plat')
    user = get_current_user()
    if user is not None:
        for constituer in user.get_panier().constituer_assoc:
            if constituer.plat.nom_plat == nom_plat:
                db.session.delete(constituer)

        db.session.commit()
    return redirect(url_for('panier'))


@app.route('/supprimer_formule')
def supprimer_formule():
    libelle_formule = request.args.get('libelle_formule')
    user = get_current_user()
    if user is not None:
        for constituer in user.get_panier().constituer_formule_assoc:
            if constituer.formule.libelle_formule == libelle_formule:
                db.session.delete(constituer)

        db.session.commit()
    return redirect(url_for('panier'))

@app.route("/choix_paiement")
def choix_paiement():
    return render_template("choix_paiement.html")


@app.route("/paiement")
def paiement_cb():
    f = ...
    return render_template("paiement_cb.html", form=f)


@app.route("/paiement/validation", methods=["POST"])
def validation_paiement():
    user = get_current_user()
    if user is None:
        return redirect(url_for('login'))

    panier = user.get_panier()
    if panier is None:
        return redirect(url_for('panier'))

    try:
        panier.etat = "Non payée"
        panier.date_creation = datetime.now()

        for constituer_plat in panier.constituer_assoc:
            constituer_plat.plat.stock_utilisable -= constituer_plat.quantite_plat
        
        for constituer_formule in panier.constituer_formule_assoc:
            for plat in constituer_formule.formule.les_plats:
                plat.stock_utilisable -= constituer_formule.quantite_formule

        db.session.commit()

    except Exception as e:
        flash("Erreur : " + str(e), "danger")
        return redirect(url_for('panier'))

    return render_template("validation_commande.html", panier=panier)
