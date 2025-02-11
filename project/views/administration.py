from project import app, db
from flask import render_template, url_for, redirect, request, flash
from project.models import Formule, Plats
from flask_wtf import FlaskForm
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from project.models import Commandes, User, Plats, get_allergenes, get_allergenes_plat
from functools import wraps
from wtforms import SelectMultipleField, StringField, PasswordField, EmailField, HiddenField, FileField, FloatField, SelectField
from wtforms.widgets import CheckboxInput, ListWidget
from wtforms_sqlalchemy.fields import QuerySelectMultipleField
from flask_wtf.file import FileAllowed
from wtforms.validators import DataRequired, EqualTo, Email, Length, Regexp, NumberRange
from werkzeug.utils import secure_filename
import os
from project.app import mkpath
import uuid
from project.models import Allergenes


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
    nom = StringField(
        "Nom du plat",
        validators=[
            DataRequired(message="Le nom du plat est requis."),
            Length(max=32, message="Le nom du plat doit contenir au maximum 32 caractères.")
        ]
    )

    prix = FloatField(
        "Prix",
        validators=[
            DataRequired(message="Le prix est requis."),
            NumberRange(min=0, message="Le prix doit être un nombre positif.")
        ]
    )

    type = SelectField(
        "Type de plat",
        choices=[
            ("Plat chaud", "Plat chaud"),
            ("Plat froid", "Plat froid"),
            ("Sushi", "Sushi"),
            ("Dessert", "Dessert")
        ],
        validators=[DataRequired(message="Le type de plat est requis.")]
    )

    allergenes = QuerySelectMultipleField(
        "Allergènes",
        query_factory=lambda: get_allergenes(),
        get_label="nom_allergene",
        widget=ListWidget(prefix_label=False),
        option_widget=CheckboxInput()
    )

    img = FileField(
        "Image",
        validators=[
            FileAllowed(["jpg", "jpeg", "png", "gif"], message="Seules les images au format JPG, JPEG, PNG ou GIF sont autorisées.")
        ]
    )

class FormuleForm(FlaskForm):
    libelle_formule = StringField("Nom de la formule", validators=[DataRequired(), Length(max=64)])
    prix = FloatField("Prix", validators=[DataRequired()])
    plats = SelectMultipleField("Plats", coerce=str, validators=[DataRequired()])
    csrf_token = HiddenField()


@app.route("/admin")
@admin_required
def admin():
    # Tables disponibles aujourd'hui
    commandes_sur_place = Commandes.get_sur_place_at()
    dico_tables = {i: False for i in range(1, 13)}
    for table in commandes_sur_place :
        dico_tables[table.num_table] = True

    # Blacklist
    liste_noire = User.get_blackliste()
    return render_template("admin_traiteur.html", tables = dico_tables, blacklist = liste_noire)

@app.route("/admin/blacklist", methods = ["GET", "POST"])
def blackliste_supprimer() :
    user = User.get_user(request.args.get('id_client'))
    user.blackliste =  False
    db.session.commit()
    return admin()

@app.route("/suivi/commande")
@admin_required
def suivi_commande():
    commandes = Commandes.get_commandes_today()
    return render_template("suivi_commandes.html", les_commandes=commandes)

@app.route("/suivi/stock")
@admin_required
def suivi_stock() :
    plats_chauds=Plats.get_plats_chauds()
    plats_froids=Plats.get_plats_froids()
    sushis=Plats.get_sushis()
    desserts=Plats.get_desserts()
    return render_template("suivi_stock.html",plats_froids=plats_froids, plats_chauds=plats_chauds, sushis=sushis, desserts=desserts )

@app.route("/modifier_stock", methods=["POST"])
def modifier_stock():
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
    category = request.form.get('category')
    print(category)
    if category == "plats_chauds":
        print(1)
        # Réinitialiser les plats chauds
        for plat in Plats.query.filter_by(type_plat="Plat chaud"):
            print(plat)
            plat.stock_utilisable = plat.quantite_defaut
            plat.stock_reserve = int(plat.quantite_defaut * 0.2)
    elif category == "plats_froids":
        print(2)
        # Réinitialiser les plats froids
        for plat in Plats.query.filter_by(type_plat="Plat froid"):
            plat.stock_utilisable = plat.quantite_defaut
            plat.stock_reserve = int(plat.quantite_defaut * 0.2)
    elif category == "sushis":
        # Réinitialiser les sushis
        for plat in Plats.query.filter_by(type_plat="Sushi"):
            plat.stock_utilisable = plat.quantite_defaut
            plat.stock_reserve = int(plat.quantite_defaut * 0.2)
    elif category == "desserts":
        # Réinitialiser les desserts
        for plat in Plats.query.filter_by(type_plat="Dessert"):
            plat.stock_utilisable = plat.quantite_defaut
            plat.stock_reserve = int(plat.quantite_defaut * 0.2)

    db.session.commit()
    return redirect(url_for('suivi_stock'))  # Redirige vers la page principale des stocks


@app.route("/creation/plat", methods=["GET"])
@admin_required
def creation_plat():
    form = PlatForm()
    return render_template("creation_plat.html", form=form, allergenes=get_allergenes())


@app.route("/creation/offre", methods=["GET"])
@admin_required
def creation_offre():
    form = FormuleForm()
    form.plats.choices = [(plat.nom_plat, plat.nom_plat) for plat in Plats.get_plats()]
    return render_template("creation_offre.html", form=form, plats=Plats.get_plats())

@app.route("/add_offre", methods=["POST"])
@admin_required
def add_offre():
    libelle_formule = request.form.get("libelle_formule")
    prix = request.form.get("prix")
    plats_selectionnes = request.form.getlist("plats")  # Récupère tous les plats sélectionnés

    # Validation : Vérifie que tous les champs sont remplis
    if not libelle_formule or not prix or not plats_selectionnes:
        flash("Erreur : Veuillez remplir tous les champs et sélectionner au moins un plat.", "danger")
        return redirect(url_for("creation_offre"))

    # Validation du nombre de plats
    if len(plats_selectionnes) > 4:
        flash("Erreur : Une formule ne peut contenir que 4 plats maximum.", "danger")
        return redirect(url_for("creation_offre"))

    # Vérifier si la formule existe déjà
    formule_existante = Formule.query.filter_by(libelle_formule=libelle_formule).first()
    if formule_existante:
        flash(f"Erreur : La formule '{libelle_formule}' existe déjà.", "danger")
        return redirect(url_for("creation_offre"))

    # Créer une nouvelle formule
    nouvelle_formule = Formule(
        libelle_formule=libelle_formule,
        prix=prix
    )

    # Ajouter les plats sélectionnés
    for nom_plat in plats_selectionnes:
        plat = Plats.query.filter_by(nom_plat=nom_plat).first()
        if plat:
            nouvelle_formule.les_plats.append(plat)

    db.session.add(nouvelle_formule)
    db.session.commit()

    flash(f"La formule '{libelle_formule}' a été ajoutée avec succès.", "success")
    return redirect(url_for("creation_offre"))

@app.route("/update_offre/<int:id>", methods=["POST"])
@admin_required
def update_offre(id):
    formule = Formule.query.get(id)
    libelle_formule = request.form.get("libelle_formule")
    prix = request.form.get("prix")
    plats_selectionnes = request.form.getlist("plats")

    if not libelle_formule or not prix or len(plats_selectionnes) > 4:
        flash("Erreur : Veuillez remplir tous les champs et sélectionner jusqu'à 4 plats.", "danger")
        return redirect(url_for("edition_offre"))

    formule.libelle_formule = libelle_formule
    formule.prix = prix
    formule.les_plats = [Plats.query.filter_by(nom_plat=nom).first() for nom in plats_selectionnes]

    db.session.commit()
    flash(f"La formule '{libelle_formule}' a été modifiée avec succès.", "success")
    return redirect(url_for("edition_offre"))

@app.route("/delete_offre/<int:id>", methods=["POST"])
@admin_required
def delete_offre(id):
    formule = Formule.query.get(id)
    db.session.delete(formule)
    db.session.commit()
    flash("La formule a été supprimée avec succès.", "success")
    return redirect(url_for("edition_offre"))

@app.route("/edition/plat")
@admin_required
def edition_plat():
    type = request.args.get('type', 'a')
    plats = Plats.get_plats()
    plats_chauds = Plats.get_plats_chauds()
    plats_froids = Plats.get_plats_froids()
    sushis = Plats.get_sushis()
    desserts = Plats.get_desserts()
    allergenes = get_allergenes()
    
    return render_template(
        "edition_plat.html",
        plats=plats,
        plats_chauds=plats_chauds,
        plats_froids=plats_froids,
        sushis=sushis,
        desserts=desserts,
        allergenes=allergenes,
        type=type
        )
    
@app.route("/update_plat/<string:id>", methods=["POST"])
@admin_required
def update_plat(id):
    # Récupérer le plat depuis la base de données
    plat = Plats.query.get_or_404(id)

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
    plat.prix = float(request.form['prix'])

    # Récupérer les allergènes cochés
    allergenes_selectionnes = request.form.getlist('allergenes[]')

    # Rechercher les objets `Allergenes` correspondants
    allergenes = Allergenes.query.filter(Allergenes.nom_allergene.in_(allergenes_selectionnes)).all()

    # Mettre à jour la relation Many-to-Many
    plat.les_allergenes = allergenes

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
        allergenes = form.allergenes.data
        print(allergenes)

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
        plat.add_allergene(allergenes)
        db.session.add(plat)
        db.session.commit()

        flash(f"Le plat '{nom_plat}' a été ajouté avec succès.", "success")
        return redirect(url_for('edition_plat'))

    return render_template('creation_plat.html', form=form)

@app.route("/edition/offre")
@admin_required
def edition_offre():
    type = request.args.get('type', 'a')
    formules = Formule.query.all()
    plats = Plats.query.all()
    return render_template("edition_offre.html", formules=formules, plats=plats, type=type)
