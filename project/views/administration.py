from project import app, db
from flask import render_template, url_for, redirect, request, flash
#from .models import
from flask_wtf import FlaskForm
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from functools import wraps

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash("Vous devez être administrateur pour accéder à cette page.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/admin")
@admin_required
def admin():
    return render_template("admin_traiteur.html")

@app.route("/suivi/commande")
@admin_required
def suivi_commande() :
    return render_template("suivi_commandes.html")

@app.route("/suivi/stock")
@admin_required
def suivi_stock() :
    return render_template("suivi_stock.html")

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
    return render_template("edition_plat.html")

@app.route("/edition/offre")
@admin_required
def edition_offre():
    return render_template("edition_offre.html")