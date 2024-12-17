from project import app, db
from flask import render_template, url_for, redirect, request, flash
from project.models import Plats
from flask_wtf import FlaskForm
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from project.models import Commandes, User, get_sur_place_today, get_blackliste, get_user, get_commandes_today, get_desserts, get_plats_chauds, get_plats_froids, get_sushis, Plats
from functools import wraps
from wtforms import StringField, PasswordField, EmailField, HiddenField
from wtforms.validators import DataRequired, EqualTo, Email, Length, Regexp

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash("Vous devez être administrateur pour accéder à cette page.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function

class PlatForm(FlaskForm):
    nom = StringField("Nom", validators=[DataRequired(), 
                                          Length(max=32)])
    prix = StringField("Prix", validators=[DataRequired(), 
                                                   Length(max=32)])


@app.route("/admin")
@admin_required
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
@admin_required
def suivi_commande():
    commandes = get_commandes_today()
    return render_template("suivi_commandes.html", les_commandes=commandes)

@app.route("/suivi/stock")
@admin_required
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

@app.route('/reinitialiser_stock', methods=['POST'])
def reinitialiser_stock():
    category = request.form.get('category')
    print(category)
    if category == "plats_chauds":
        print(1)
        # Réinitialiser les plats chauds
        for plat in Plats.query.filter_by(type_plat="Plat chaud"):
            print(plat)
            plat.quantite_stock = plat.quantite_defaut
    elif category == "plats_froids":
        print(2)
        # Réinitialiser les plats froids
        for plat in Plats.query.filter_by(type_plat="Plat froid"):
            plat.quantite_stock = plat.quantite_defaut
    elif category == "sushis":
        # Réinitialiser les sushis
        for plat in Plats.query.filter_by(type_plat="Sushi"):
            plat.quantite_stock = plat.quantite_defaut
    elif category == "desserts":
        # Réinitialiser les desserts
        for plat in Plats.query.filter_by(type_plat="Dessert"):
            plat.quantite_stock = plat.quantite_defaut

    db.session.commit()
    return redirect(url_for('suivi_stock'))  # Redirige vers la page principale des stocks


@app.route("/creation/plat")
@admin_required
def creation_plat():
    return render_template("creation_plat.html")

@app.route("/creation/offre")
@admin_required
def creation_offre():
    return render_template("creation_offre.html")

@app.route("/edition/plat")
@admin_required
def edition_plat():
    return render_template(
        "edition_plat.html",
        plats=Plats.get_all_plats(Plats)
        )

@app.route("/edition/offre")
@admin_required
def edition_offre():
    return render_template("edition_offre.html")
