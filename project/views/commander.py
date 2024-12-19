from project import app, db
from flask import render_template, url_for, redirect, request, make_response
#from .models import
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import BooleanField, SubmitField, StringField
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from project.models import get_desserts, get_plats, get_formules, get_allergenes, get_desserts_filtered_by_allergenes, get_plats_chauds_filtered_by_allergenes, get_plats_froids_filtered_by_allergenes, get_formules_filtered_by_allergenes, get_plats_filtered_by_allergenes, get_sushis_filtered_by_allergenes


class AllergeneForm(FlaskForm):
    allergene = BooleanField('Allergène', validators=[DataRequired()])
    type = StringField('Type', validators=[DataRequired()])
    submit = SubmitField('Filtrer')

@app.route("/commander", methods=["GET", "POST"])
def commander():
    form = AllergeneForm()  
    selected_allergenes = request.form.getlist('allergenes')  # Liste des allergènes cochés
    type = request.args.get('type', 'p')
    allergenes = get_allergenes()
    plats = get_plats_filtered_by_allergenes(selected_allergenes)
    plats_chauds = get_plats_chauds_filtered_by_allergenes(selected_allergenes)
    plats_froids = get_plats_froids_filtered_by_allergenes(selected_allergenes)
    sushi = get_sushis_filtered_by_allergenes(selected_allergenes)
    formules = get_formules_filtered_by_allergenes(selected_allergenes)
    desserts = get_desserts_filtered_by_allergenes(selected_allergenes)

    return render_template("commander.html", 
                           plats=plats, 
                            plats_chauds=plats_chauds,
                            plats_froids=plats_froids,
                            sushi=sushi,
                           formules=formules, 
                           desserts=desserts, 
                           type=type, 
                           nb_plats=len(plats), 
                           nb_formules=len(formules), 
                           nb_desserts=len(desserts), 
                           allergenes=allergenes, 
                           selected_allergenes=selected_allergenes,
                           form=form)
    
@app.route("/filter_allergenes", methods=["GET", "POST"])
def filter_allergenes():
    form = AllergeneForm()
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
    
   
        
    allergenes = get_allergenes()
    plats = get_plats_filtered_by_allergenes(selected_allergenes)
    plats_chauds = get_plats_chauds_filtered_by_allergenes(selected_allergenes)
    plats_froids = get_plats_froids_filtered_by_allergenes(selected_allergenes)
    sushi = get_sushis_filtered_by_allergenes(selected_allergenes)
    formules = get_formules_filtered_by_allergenes(selected_allergenes)
    desserts = get_desserts_filtered_by_allergenes(selected_allergenes)
    
    
        

    resp = make_response(render_template("commander.html", 
                           plats=plats, 
                            plats_chauds=plats_chauds,
                            plats_froids=plats_froids,
                            sushi=sushi,
                           type=type,
                           allergenes=allergenes,
                           formules=formules, 
                           desserts=desserts, 
                           selected_allergenes=selected_allergenes,
                           form=form))
    
    if request.method == "POST":
        string_allergenes = ""
        for al in selected_allergenes:
            string_allergenes += str(al) + ","
        resp.set_cookie('allergenes', string_allergenes)
    # Rendre la page commander avec les données filtrées
    return resp


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
