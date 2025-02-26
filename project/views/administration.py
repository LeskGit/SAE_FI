"""
Ce module gère les fonctionnalités de l'administrateur de l'application, 
y compris la création et la modification des plats et des formules, 
ainsi que le suivi des stocks et des commandes.
"""
import os
import uuid
from functools import wraps
from hashlib import sha256

from flask import render_template, url_for, redirect, request, flash
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from project.models import Commandes, User, Plats, Allergenes, Reduction
from functools import wraps
from wtforms import SelectMultipleField, StringField, PasswordField, EmailField, HiddenField, FileField, FloatField, SelectField
from flask_wtf.file import FileAllowed
from werkzeug.utils import secure_filename
from wtforms import SelectMultipleField, StringField, HiddenField, FileField, FloatField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange
from wtforms.widgets import CheckboxInput, ListWidget
from wtforms_sqlalchemy.fields import QuerySelectMultipleField

from project import app, db
from project.models import Commandes, User, Plats, Allergenes, Formule
from project.app import mkpath


def admin_required(f):

    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash("Vous devez être administrateur pour accéder à cette page.",
                  "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)

    return decorated_function


class PlatForm(FlaskForm):
    """Formulaire pour les plats
    """
    nom = StringField(
        "Nom du plat",
        validators=[
            DataRequired(message="Le nom du plat est requis."),
            Length(
                max=32,
                message="Le nom du plat doit contenir au maximum 32 caractères."
            )
        ])

    prix = FloatField("Prix",
                      validators=[
                          DataRequired(message="Le prix est requis."),
                          NumberRange(
                              min=0,
                              message="Le prix doit être un nombre positif.")
                      ])

    type = SelectField(
        "Type de plat",
        choices=[("Plat chaud", "Plat chaud"), ("Plat froid", "Plat froid"),
                 ("Sushi", "Sushi"), ("Dessert", "Dessert")],
        validators=[DataRequired(message="Le type de plat est requis.")])

    allergenes = QuerySelectMultipleField(
        "Allergènes",
        query_factory=lambda: Allergenes.get_allergenes(),
        get_label="nom_allergene",
        widget=ListWidget(prefix_label=False),
        option_widget=CheckboxInput())

    img = FileField(
        "Image",
        validators=[
            FileAllowed(
                ["jpg", "jpeg", "png", "gif"],
                message=
                "Seules les images au format JPG, JPEG, PNG ou GIF sont autorisées."
            )
        ])


class FormuleForm(FlaskForm):
    """Formulaire pour les formules
    """
    libelle_formule = StringField("Nom de la formule",
                                  validators=[DataRequired(),
                                              Length(max=64)])
    prix = FloatField("Prix", validators=[DataRequired()])
    plats = SelectMultipleField("Plats",
                                coerce=str,
                                validators=[DataRequired()])
    csrf_token = HiddenField()


@app.route("/admin")
@admin_required
def admin():
    """fonction permettant de récupérer 
    les tables disponibles ou non et la blacklist

    Returns:
        template: la page d'accueil de l'admin
    """
    # Tables disponibles aujourd'hui
    commandes_sur_place = Commandes.get_sur_place_at()
    dico_tables = {i: False for i in range(1, 13)}
    for table in commandes_sur_place:
        dico_tables[table.num_table] = True

    # Blacklist
    liste_noire = User.get_blackliste()
    return render_template("admin_traiteur.html",
                           tables=dico_tables,
                           blacklist=liste_noire)


@app.route("/admin/blacklist", methods=["GET", "POST"])
def blackliste_supprimer():
    """fonction permettant de supprimer 
    de la blacklist un User

    Returns:
        template : la page d'accueil de l'admin
    """
    user = User.get_user(request.args.get('id_client'))
    user.blackliste = False
    db.session.commit()
    return redirect(url_for('admin'))


@app.route("/suivi/commande")
@admin_required
def suivi_commande():
    """fonction qui récupère les commandes 
    et renvoie la page html su suivi des commandes

    Returns:
        template: la page de suivi des commandes
    """
    commandes = Commandes.get_commandes_today()
    return render_template("suivi_commandes.html", les_commandes=commandes)


@app.route("/suivi/stock")
@admin_required
def suivi_stock():
    """fonction qui récupère les différents plats 
    et renvoie la page de suivi des stocks

    Returns:
        template: la page de suivi des stocks
    """
    plats_chauds = Plats.get_plats_chauds()
    plats_froids = Plats.get_plats_froids()
    sushis = Plats.get_sushis()
    desserts = Plats.get_desserts()
    return render_template("suivi_stock.html",
                           plats_froids=plats_froids,
                           plats_chauds=plats_chauds,
                           sushis=sushis,
                           desserts=desserts)


@app.route("/modifier_stock", methods=["POST"])
def modifier_stock():
    """fonction permettant de modifier les stocks

    Returns:
        template: la page de suivi des stocks
    """
    for key, value in request.form.items():
        nom_plat = key
        nouveau_stock = int(value)
        plat = db.session.query(Plats).filter_by(nom_plat=nom_plat).one()
        plat.stock_utilisable = nouveau_stock
        plat.stock_reserve = int(nouveau_stock * 0.2)
        db.session.commit()
    return redirect(url_for("suivi_stock"))


@app.route('/reinitialiser_stock', methods=['POST'])
def reinitialiser_stock():
    """fonction permettant de réinitialiser 
    les stocks d'un type de plat

    Returns:
        template: la page de suivi des stocks
    """
    category = request.form.get('category')
    for plat in Plats.query.filter_by(type_plat=category):
        plat.stock_utilisable = plat.quantite_defaut
        plat.stock_reserve = int(plat.quantite_defaut * 0.2)

    db.session.commit()
    return redirect(
        url_for('suivi_stock'))  # Redirige vers la page principale des stocks


@app.route("/creation/plat", methods=["GET"])
@admin_required
def creation_plat():
    """fonction pour la page de création de plat

    Returns:
        template: template de création de plat
    """
    form = PlatForm()
    return render_template("creation_plat.html",
                           form=form,
                           allergenes=Allergenes.get_allergenes())

@app.route("/edition/plat")
@admin_required
def edition_plat():
    """fonction pour la page d'édition de plat

    Returns:
        template: template d'édition de plat
    """
    type = request.args.get('type', 'a')
    query_plats = request.args.get('query')
    plats = Plats.query.filter(Plats.nom_plat.like(f"%{query_plats}%")).all(
    ) if query_plats is not None else Plats.get_plats()
    plats_chauds = Plats.get_plats_chauds()
    plats_froids = Plats.get_plats_froids()
    sushis = Plats.get_sushis()
    desserts = Plats.get_desserts()
    allergenes = Allergenes.get_allergenes()

    return render_template("edition_plat.html",
                           plats=plats,
                           plats_chauds=plats_chauds,
                           plats_froids=plats_froids,
                           sushis=sushis,
                           desserts=desserts,
                           allergenes=allergenes,
                           type=type)

@app.route("/ajout_plat", methods=["GET", "POST"])
@admin_required
def add_plat():
    """fonction qui permet de créer un plat

    Returns:
        template: le template d'édition de plat si la création 
        s'est déroulée sans accroc, celle de création de plat sinon
    """
    form = PlatForm()
    if form.validate_on_submit():

        # Récupération des données du formulaire
        nom_plat = form.nom.data
        prix = form.prix.data
        type_plat = form.type.data
        img = form.img.data
        allergenes = form.allergenes.data
        print(allergenes)

        # Validation des données
        if not nom_plat or not prix or not type_plat:
            flash("Erreur : Les champs nom, prix et type sont requis.",
                  "danger")
            return render_template('creation_plat.html', form=form)

        # Vérifier si le plat existe déjà
        plat = Plats.query.filter_by(nom_plat=nom_plat).first()
        if plat:
            flash(f"Erreur : Le plat '{nom_plat}' existe déjà.", "danger")
            return render_template('creation_plat.html', form=form)

        # Enregistrement de l'image
        if img:
            filename = secure_filename(img.filename)
            upload_folder = mkpath(
                'static/img/product'
            )  # Utilisation de mkpath pour récupérer le chemin absolu du dossier
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)  # Crée le dossier s'il n'existe pas

            img.save(os.path.join(upload_folder, filename))
        else:
            filename = None

        # Création du plat
        plat = Plats(nom_plat=nom_plat,
                     prix=prix,
                     type_plat=type_plat,
                     img=filename)
        plat.add_allergene(allergenes)
        db.session.add(plat)
        db.session.commit()

        flash(f"Le plat '{nom_plat}' a été ajouté avec succès.", "success")
        return redirect(url_for('edition_plat'))

    return render_template('creation_plat.html', form=form)

@app.route("/update_plat/<string:id>", methods=["POST"])
@admin_required
def update_plat(id):
    """fonction pour modifier un plat

    Args:
        id (str): l'id du plat

    Returns:
        template: le template d'édition de plat
    """
    # Récupérer le plat depuis la base de données
    plat = Plats.query.get_or_404(id)

    # Récupérer le fichier image
    if 'img' in request.files:
        file = request.files['img']
        if file:
            # Sauvegarder le fichier avec un nom unique
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            img_path = os.path.join(app.config['UPLOAD_FOLDER'],
                                    unique_filename)

            # Sauvegarder l'image dans le dossier 'static/img'
            file.save(img_path)

            # Mettre à jour le champ img du plat
            plat.img = f"{unique_filename}"

    # Mettre à jour les autres champs du plat
    plat.nom_plat = request.form['nom_plat']
    plat.type_plat = request.form['type_plat']
    plat.prix = float(request.form['prix'])

    # Récupérer les allergènes cochés
    allergenes_selectionnes = request.form.getlist('allergenes[]')

    # Rechercher les objets `Allergenes` correspondants
    allergenes = Allergenes.query.filter(
        Allergenes.nom_allergene.in_(allergenes_selectionnes)).all()

    # Mettre à jour la relation Many-to-Many
    plat.les_allergenes = allergenes

    # Enregistrer les modifications dans la base de données
    db.session.commit()

    return redirect(url_for('edition_plat'))


@app.route("/delete_plat/<string:id>", methods=["POST"])
@admin_required
def delete_plat(id):
    """fonction pour supprimer un plat

    Args:
        id (str): l'id du plat à supprimer

    Returns:
        template: le template d'édition de plat
    """
    # Récupérer le plat par son ID
    plat = db.session.query(Plats).filter_by(nom_plat=id).first()
    if not plat:
        return f"Erreur : Le plat '{id}' n'existe pas.", 404

    # Supprimer le plat
    try:
        db.session.delete(plat)
        db.session.commit()
        flash(f"Le plat '{id}' a été supprimé avec succès.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur : Le plat est déjà dans une commande", "danger")

    # Retourner la liste mise à jour des plats
    return redirect(url_for('edition_plat'))

@app.route("/creation/offre", methods=["GET"])
@admin_required
def creation_offre():
    """fonction pour la page de création d'offre

    Returns:
        template: template de création d'offre
    """
    form = FormuleForm()
    form.plats.choices = [
        (plat.nom_plat, plat.nom_plat) for plat in Plats.get_plats()
    ]
    return render_template("creation_offre.html",
                           form=form,
                           plats=Plats.get_plats())

@app.route("/edition/offre")
@admin_required
def edition_offre():
    """fonction pour la page d'édition d'offre

    Returns:
        template: template d'édition d'offre
    """
    type = request.args.get('type', 'a')
    formules = Formule.query.all()
    plats = Plats.query.all()
    return render_template("edition_offre.html",
                           formules=formules,
                           plats=plats,
                           type=type)

@app.route("/admin/creation_promo", methods=["GET", "POST"])
@admin_required
def creation_promo():
    if request.method == "POST":
        #TODO: Ajouter la réduction dans la base de données
        pass
    plats = Plats.query.all()
    return render_template("creation_promo.html", plats=plats)

@app.route("/admin/edition_promo", methods=["GET"])
@admin_required
def edition_promo():
    """
    Liste et gère (modifier/supprimer) les réductions existantes.
    """
    promo = Reduction.query.all()
    all_plats = Plats.query.all()

    return render_template("edition_promo.html",
                           promo=promo,
                           all_plats=all_plats)

@app.route("/admin/creation_reduc", methods=["GET", "POST"])
@admin_required
def creation_reduction():
    if request.method == "POST":
        id_plat = request.form.get("id_plat")
        pourcentage = request.form.get("reduction")
        cost_points = request.form.get("points_fidelite")
        if not id_plat or not pourcentage or not cost_points:
            flash("Formulaire incomplet.", "danger")
            return redirect(url_for("creation_reduction"))

        try:
            new_reduc = Reduction(
                id_plat=int(id_plat),
                reduction=int(pourcentage),
                points_fidelite=int(cost_points)
            )
            db.session.add(new_reduc)
            db.session.commit()
            flash("Réduction créée avec succès.", "success")
            return redirect(url_for("edition_reduction"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la création: {e}", "danger")
            return redirect(url_for("creation_reduction"))

    plats = Plats.query.all()
    return render_template("creation_reduc.html", plats=plats)


@app.route("/admin/edition_reduc", methods=["GET"])
@admin_required
def edition_reduction():
    """
    Liste et gère (modifier/supprimer) les réductions existantes.
    """
    reductions = Reduction.query.all()
    all_plats = Plats.query.all()
    plats_map = {p.id_plat: p for p in all_plats}

    return render_template("edition_reduc.html",
                           reductions=reductions,
                           plats_map=plats_map,
                           all_plats=all_plats)


@app.route("/admin/update_reduction/<int:id_reduction>", methods=["POST"])
@admin_required
def update_reduction(id_reduction):
    """
    Met à jour une réduction existante (changement de plat, pourcentage, coût en points).
    """
    reduc = Reduction.query.get_or_404(id_reduction)
    try:
        new_plat_id = int(request.form.get("id_plat"))
        new_pourcentage = int(request.form.get("reduction"))
        new_points = int(request.form.get("points_fidelite"))

        reduc.id_plat = new_plat_id
        reduc.reduction = new_pourcentage
        reduc.points_fidelite = new_points

        db.session.commit()
        flash("Réduction mise à jour avec succès.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la modification: {e}", "danger")

    return redirect(url_for("edition_reduction"))


@app.route("/admin/delete_reduction/<int:id_reduction>", methods=["POST"])
@admin_required
def delete_reduction(id_reduction):
    """
    Supprime une réduction (bouton 'Supprimer').
    """
    reduc = Reduction.query.get_or_404(id_reduction)
    try:
        db.session.delete(reduc)
        db.session.commit()
        flash("Réduction supprimée avec succès.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression: {e}", "danger")

    return redirect(url_for("edition_reduction"))

@app.route("/add_offre", methods=["POST"])
@admin_required
def add_offre():
    """fonction permettant d'ajouter une offre

    Returns:
        template: le template de création d'offre
    """
    libelle_formule = request.form.get("libelle_formule")
    prix = request.form.get("prix")
    plats_selectionnes = request.form.getlist(
        "plats")  # Récupère tous les plats sélectionnés

    # Validation : Vérifie que tous les champs sont remplis
    if not libelle_formule or not prix or not plats_selectionnes:
        flash(
            "Erreur : Veuillez remplir tous les champs et sélectionner au moins un plat.",
            "danger")
        return redirect(url_for("creation_offre"))

    # Validation du nombre de plats
    if len(plats_selectionnes) > 4:
        flash("Erreur : Une formule ne peut contenir que 4 plats maximum.",
              "danger")
        return redirect(url_for("creation_offre"))

    # Vérifier si la formule existe déjà
    formule_existante = Formule.query.filter_by(
        libelle_formule=libelle_formule).first()
    if formule_existante:
        flash(f"Erreur : La formule '{libelle_formule}' existe déjà.", "danger")
        return redirect(url_for("creation_offre"))

    # Créer une nouvelle formule
    nouvelle_formule = Formule(libelle_formule=libelle_formule, prix=prix)

    # Ajouter les plats sélectionnés
    for nom_plat in plats_selectionnes:
        plat = Plats.query.filter_by(nom_plat=nom_plat).first()
        if plat:
            nouvelle_formule.les_plats.append(plat)

    db.session.add(nouvelle_formule)
    db.session.commit()

    flash(f"La formule '{libelle_formule}' a été ajoutée avec succès.",
          "success")
    return redirect(url_for("creation_offre"))


@app.route("/update_offre/<int:id>", methods=["POST"])
@admin_required
def update_offre(id):
    """fonction pour modifier une offre

    Args:
        id (str): l'id de l'offre

    Returns:
        template: le template d'édition de l'offre
    """
    formule = Formule.query.get(id)
    libelle_formule = request.form.get("libelle_formule")
    prix = request.form.get("prix")
    plats_selectionnes = request.form.getlist("plats")

    if not libelle_formule or not prix or len(plats_selectionnes) > 4:
        flash(
            "Erreur : Veuillez remplir tous les champs et sélectionner jusqu'à 4 plats.",
            "danger")
        return redirect(url_for("edition_offre"))

    formule.libelle_formule = libelle_formule
    formule.prix = prix
    formule.les_plats = [
        Plats.query.filter_by(nom_plat=nom).first()
        for nom in plats_selectionnes
    ]

    db.session.commit()
    flash(f"La formule '{libelle_formule}' a été modifiée avec succès.",
          "success")
    return redirect(url_for("edition_offre"))


@app.route("/delete_offre/<int:id>", methods=["POST"])
@admin_required
def delete_offre(id):
    """fonction pour supprimer une offre

    Args:
        id (str): l'id de l'offre à supprimer

    Returns:
        template: le template d'édition d'offre
    """
    formule = Formule.query.get(id)
    db.session.delete(formule)
    db.session.commit()
    flash("La formule a été supprimée avec succès.", "success")
    return redirect(url_for("edition_offre"))

