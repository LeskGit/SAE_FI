from project import app, db
from flask import render_template, url_for, redirect, request, flash
from project.models import Plats, get_plats
from flask_wtf import FlaskForm
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from project.models import Commandes, User, get_sur_place_today, get_blackliste, get_user, get_commandes_today, get_desserts, get_plats_chauds, get_plats_froids, get_sushis, Plats
from functools import wraps
from wtforms import StringField, PasswordField, EmailField, HiddenField, FileField, FloatField
from flask_wtf.file import FileAllowed
from wtforms.validators import DataRequired, EqualTo, Email, Length, Regexp
from werkzeug.utils import secure_filename
import os
from project.app import mkpath
import uuid


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
    nom = StringField("Nom du plat", validators=[DataRequired(), Length(max=32)])
    prix = FloatField("Prix", validators=[DataRequired()])
    type = StringField("Type de plat", validators=[DataRequired(), Length(max=32)])
    img = FileField("Image", validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    csrf_token = HiddenField()



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


@app.route("/creation/plat", methods=["GET"])
@admin_required
def creation_plat():
    form = PlatForm()
    return render_template("creation_plat.html", form=form)


@app.route("/creation/offre")
@admin_required
def creation_offre():
    return render_template("creation_offre.html")

@app.route("/edition/plat")
@admin_required
def edition_plat():
    type = request.args.get('type', 'a')
    plats = get_plats()
    plats_chauds = get_plats_chauds()
    plats_froids = get_plats_froids()
    sushis = get_sushis()
    desserts = get_desserts()
    
    return render_template(
        "edition_plat.html",
        plats=plats,
        plats_chauds=plats_chauds,
        plats_froids=plats_froids,
        sushis=sushis,
        desserts=desserts,
        type=type
        )
    
@app.route("/update_plat/<string:id>", methods=["POST"])
@admin_required
def update_plat(id):
    # Récupérer le plat depuis la base de données (exemple)
    plat = Plats.query.get(id)

    # Récupérer le fichier image
    if 'img' in request.files:
        file = request.files['img']
        if file:
            # Sauvegarder le fichier avec un nom unique
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

            # Sauvegarder l'image dans le dossier 'static/img'
            file.save(img_path)

            # Mettre à jour le champ img du plat
            plat.img = f"{unique_filename}"

    # Mettre à jour les autres champs du plat
    plat.nom_plat = request.form['nom_plat']
    plat.type_plat = request.form['type_plat']
    plat.prix = request.form['prix']

    # Enregistrer les modifications dans la base de données
    db.session.commit()

    return redirect(url_for('edition_plat'))

@app.route("/delete_plat/<string:id>", methods=["POST"])
@admin_required
def delete_plat(id):
    # Récupérer le plat par son ID
    plat = db.session.query(Plats).filter_by(nom_plat=id).first()
    if not plat:
        return f"Erreur : Le plat '{id}' n'existe pas.", 404

    # Supprimer le plat
    db.session.delete(plat)
    db.session.commit()

    # Retourner la liste mise à jour des plats
    return redirect(url_for('edition_plat'))

@app.route("/ajout_plat", methods=["GET", "POST"])
@admin_required
def add_plat():
    form = PlatForm()
    if form.validate_on_submit():

        # Récupération des données du formulaire
        nom_plat = form.nom.data
        prix = form.prix.data
        type_plat = form.type.data
        img = form.img.data

        # Validation des données
        if not nom_plat or not prix or not type_plat:
            flash("Erreur : Les champs nom, prix et type sont requis.", "danger")
            return render_template('creation_plat.html', form=form)
        
        # Vérifier si le plat existe déjà
        plat = Plats.query.filter_by(nom_plat=nom_plat).first()
        if plat:
            flash(f"Erreur : Le plat '{nom_plat}' existe déjà.", "danger")
            return render_template('creation_plat.html', form=form)

        # Enregistrement de l'image
        if img:
            filename = secure_filename(img.filename)
            upload_folder = mkpath('static/img/product')  # Utilisation de mkpath pour récupérer le chemin absolu du dossier
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)  # Crée le dossier s'il n'existe pas

            img.save(os.path.join(upload_folder, filename))
        else:
            filename = None

        # Création du plat
        plat = Plats(
            nom_plat=nom_plat,
            prix=prix,
            type_plat=type_plat,
            img=filename
        )
        db.session.add(plat)
        db.session.commit()

        flash(f"Le plat '{nom_plat}' a été ajouté avec succès.", "success")
        return redirect(url_for('edition_plat'))

    return render_template('creation_plat.html', form=form)

@app.route("/edition/offre")
@admin_required
def edition_offre():
    return render_template("edition_offre.html")
