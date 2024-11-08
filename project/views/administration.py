from project import app, db
from flask import render_template, url_for, redirect, request, flash
from project.models import Plats
from flask_wtf import FlaskForm
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from project.models import get_desserts, get_plats_chauds, get_plats_froids, get_sushis, Plats
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
    return render_template("admin_traiteur.html")

@app.route("/suivi/commande")
@admin_required
def suivi_commande() :
    return render_template(
        "suivi_commandes.html",
        )
    return render_template(
        "suivi_commandes.html",
        )

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

    return render_template(
        "edition_plat.html",
        plats=Plats.get_all_plats(Plats)
        )


@app.route("/edition/offre")
@admin_required
def edition_offre():
    return render_template("edition_offre.html")