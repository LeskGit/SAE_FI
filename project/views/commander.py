from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from project import app, db
from flask import flash, render_template, url_for, redirect, request, make_response, session
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import BooleanField, SubmitField, StringField
from wtforms import HiddenField, IntegerField
from wtforms.validators import DataRequired
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from project.models import Plats, Allergenes, Constituer, Commandes, Formule

class CommanderForm(FlaskForm):
    nom_plat = HiddenField()
    num_com = HiddenField()
    quantite = IntegerField(validators=[DataRequired()])

@app.route("/commander", methods=["GET", "POST"])
def commander():
    print("commander", session.get('user'))
    if not current_user.is_authenticated and session.get('user') is None:
        return redirect(url_for('login_unsafe'))
    elif not current_user.is_authenticated and session.get('user') is not None:
        user_id = session.get('user')
        user = User.query.get(user_id)
        print(user_id)
        return user_id
    else:
        commande = current_user.get_or_create_panier()
        num_commande = commande.num_commande
        form = CommanderForm()
        selected_allergenes = request.form.getlist('allergenes')  # Liste des allergènes cochés
        type = request.args.get('type', 'p')
        allergenes = Allergenes.get_allergenes()
        plats = Plats.get_plats()
        plats_chauds = Plats.get_plats_filtered_by_type_and_allergenes("Plat chaud", selected_allergenes)
        plats_froids = Plats.get_plats_filtered_by_type_and_allergenes("Plat froid", selected_allergenes)
        sushis = Plats.get_plats_filtered_by_type_and_allergenes("Sushi", selected_allergenes)
        formules = Formule.get_formules_filtered_by_allergenes(selected_allergenes)
        desserts = Plats.get_plats_filtered_by_type_and_allergenes("Dessert", selected_allergenes)

        return render_template("commander.html", 
                            plats=plats, 
                            plats_chauds=plats_chauds,
                            plats_froids=plats_froids,
                            sushis=sushis,
                            formules=formules, 
                            desserts=desserts, 
                            type=type, 
                            nb_plats=len(plats), 
                            nb_formules=len(formules), 
                            nb_desserts=len(desserts), 
                            allergenes=allergenes, 
                            selected_allergenes=selected_allergenes,
                            form=form,
                            num_com = num_commande)
    
@app.route("/filter_allergenes", methods=["GET", "POST"])
def filter_allergenes():

    if not current_user.is_authenticated:
        return redirect(url_for('commander'))
    
    # Récupérer la liste des allergènes sélectionnés
    if request.method == "POST":
        selected_allergenes = request.form.getlist('allergenes') # Liste des allergènes cochés
        
        for i in range(len(selected_allergenes)):
            selected_allergenes[i] = int(selected_allergenes[i])
    if request.method == "GET":
        selected_allergenes = request.cookies.get('allergenes')
        if selected_allergenes:
            selected_allergenes = selected_allergenes.split(',')
            for i in range(len(selected_allergenes)):
                if(selected_allergenes[i] != ""):
                    selected_allergenes[i] = int(selected_allergenes[i])
            print(selected_allergenes)
        else:
            selected_allergenes = []
            
    type = request.args.get('type', 'p')
    
    allergenes = Allergenes.get_allergenes()
    plats = Plats.get_plats_filtered_by_allergenes(selected_allergenes)
    plats_chauds = Plats.get_plats_filtered_by_type_and_allergenes("Plat chaud", selected_allergenes)
    plats_froids = Plats.get_plats_filtered_by_type_and_allergenes("Plat froid", selected_allergenes)
    sushis = Plats.get_plats_filtered_by_type_and_allergenes("Sushi", selected_allergenes)
    formules = Formule.get_formules_filtered_by_allergenes(selected_allergenes)
    desserts = Plats.get_plats_filtered_by_type_and_allergenes("Dessert", selected_allergenes)
    

    commande = current_user.get_or_create_panier()
    num_commande = commande.num_commande
    form = CommanderForm()

    resp = make_response(render_template("commander.html", 
                           plats=plats, 
                            plats_chauds=plats_chauds,
                            plats_froids=plats_froids,
                            sushis=sushis,
                           type=type,
                           allergenes=allergenes,
                           formules=formules, 
                           desserts=desserts, 
                           selected_allergenes=selected_allergenes,
                           form=form,
                           num_com = num_commande
                           ))
    
    if request.method == "POST":
        string_allergenes = ""
        for al in selected_allergenes:
            string_allergenes += str(al) + ","
        resp.set_cookie('allergenes', string_allergenes)
    # Rendre la page commander avec les données filtrées
    return resp


@app.route("/commander_plat", methods = ("POST",))
def ajout_plat() :
    if current_user :
        f = CommanderForm()
        if f.num_com.data :
            try:
                commande = Commandes.get_commande(f.num_com.data)
                constituer = Constituer.get_constituer(f.nom_plat.data, f.num_com.data)
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
        sur_place_disponible = True if Commandes.get_num_table_dispo(panier.date) != -1 else False
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
            numero_table = Commandes.get_num_table_dispo(panier.date)
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