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


@app.route("/edition/offre")
def edition_offre():
    return render_template("edition_offre.html")