from project import app, db
from flask import render_template, url_for, redirect, request, flash
from project.model.class_model import Allergenes, Commandes, User, Reduction, Plats
from flask_wtf import FlaskForm
from flask_login import login_user, current_user, logout_user, login_required
from hashlib import sha256
from project.views.authentification import RegisterForm
from wtforms import StringField, PasswordField, EmailField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Email, Length, Regexp
from datetime import datetime, timedelta
from project.app import MIN_MAX_MODIF
from project.views.commander import CommanderForm, get_current_user, get_plats_type

class PersoForm(FlaskForm):
    phone_number = StringField(
        "Téléphone",
        validators=[
            DataRequired(),
            Length(min=10, max=10, message='Longueur incorrecte.'),
            Regexp(r'^\d{10}$', message="Le numéro de téléphone est invalide.")
        ])
    name = StringField("Nom", validators=[DataRequired(), Length(max=32)])

    first_name = StringField("Prénom",
                             validators=[DataRequired(),
                                         Length(max=32)])

    address = StringField("Adresse",
                          validators=[DataRequired(),
                                      Length(max=64)])
    email = EmailField("Email",
                       validators=[
                           DataRequired(),
                           Email(message='addresse mail invalide'),
                           Length(max=64)
                       ])


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Ancien mot de passe",
                                 validators=[DataRequired()])
    new_password = PasswordField("Nouveau mot de passe",
                                 validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirmer le nouveau mot de passe",
        validators=[
            DataRequired(),
            EqualTo('new_password',
                    message="Les mots de passe ne correspondent pas")
        ])
    change_password = SubmitField("Enregistrer")


@app.route("/client/profil", methods=["GET", "POST"])
@login_required
def client_profil():
    f = PersoForm()
    pw_form = ChangePasswordForm()

    edit = request.args.get('edit', False, type=bool)

    if request.method == 'GET':
        f.phone_number.data = current_user.num_tel
        f.name.data = current_user.nom
        f.first_name.data = current_user.prenom
        f.address.data = current_user.adresse
        f.email.data = current_user.email

    if request.method == 'POST':
        if 'save_profile' in request.form and f.validate():
            tel = User.get_user(f.phone_number.data)
            if tel and tel.num_tel != current_user.num_tel:
                flash("Numéro de téléphone déjà utilisé", "danger")
                return redirect(url_for("client_profil"))
            current_user.num_tel = f.phone_number.data
            current_user.nom = f.name.data
            current_user.prenom = f.first_name.data
            current_user.adresse = f.address.data
            current_user.email = f.email.data
            db.session.commit()
            flash("Profil mis à jour avec succès", "success")
            return redirect(url_for("client_profil"))

        if 'change_password' in request.form and pw_form.validate():
            old_hash = sha256(pw_form.old_password.data.encode()).hexdigest()
            if old_hash != current_user.mdp:
                flash("Ancien mot de passe incorrect", "danger")
            else:
                new_hash = sha256(
                    pw_form.new_password.data.encode()).hexdigest()
                current_user.mdp = new_hash
                db.session.commit()
                flash("Mot de passe mis à jour avec succès", "success")
                return redirect(url_for("client_profil"))

    return render_template("profil_client_connecte.html",
                           form=f,
                           edit=edit,
                           pw_form=pw_form)


@app.route("/client/historique", methods=["GET", "POST"])
@login_required
def client_historique():
    commandes = (Commandes.get_historique(id_client=current_user.id_client))

    historique = []
    now = datetime.now()
    for com in commandes:
        if com.etat == "Payée":
            statut_label = "TERMINÉE"
            statut_class = "status-termine"
        elif com.etat == "Non payée":
            statut_label = "EN COURS"
            statut_class = "status-encours"
        elif com.etat == "Annulée":
            statut_label = "ANNULÉE"
            statut_class = "status-annule"
        
        # Récupération des plats commandés avec quantité
        plats_list = [f"{assoc.plat.nom_plat} (x{assoc.quantite_plat})" for assoc in com.constituer_assoc] if com.constituer_assoc else []

        # Récupération des formules commandées avec quantité
        formules_list = [f"{assoc.formule.libelle_formule} (x{assoc.quantite_formule})" for assoc in com.constituer_formule_assoc] if com.constituer_formule_assoc else []

        # Fusion des listes de plats et formules
        articles_commandes = plats_list + formules_list
        plats_names = ", ".join(articles_commandes) if articles_commandes else "-"

        # Calcul du prix total
        total_price = str(com.calculer_prix() + com.compute_reduction(current_user)) + " €" if articles_commandes else "-"
        
        can_modify = False
        if com.etat != "Payée":
            elapsed = now - com.date_creation
            if elapsed < timedelta(minutes=MIN_MAX_MODIF):
                can_modify = True

        historique.append({
            "num_commande": com.num_commande,
            "plat": plats_names,
            "prix": total_price,
            "statut_label": statut_label,
            "statut_class": statut_class,
            "date_str": com.date.strftime('%Y/%m/%d') if com.date else '-',
            "heure_str": com.date.strftime('%H:%M') if com.date else '-',
            "can_modify": can_modify,
            "etat": com.etat
        })

    return render_template("historique_commandes.html", historique=historique)


@app.route("/client/modif/<int:id_commande>")
@login_required
def client_modif(id_commande):
    user = get_current_user()
    if user is None:
        return redirect(url_for('login'))
    
    commande = Commandes.get_commande(id_commande)
    if commande is None:
        return redirect(url_for('client_historique'))

    commande.calculer_prix()
    commande.compute_reduction(user)
    
    if not Commandes.can_modify_commande(id_commande, user.id_client):
        return redirect(url_for('client_historique'))
    
    num_commande = id_commande
    form = CommanderForm()
    
    type = request.args.get('type', 'p')
    query_plats = request.args.get('query', "")
    
    les_plats = get_plats_type(type, [], query_plats, False)

    return render_template("modif_commande.html", 
                        list_plats=les_plats,
                        type=type,
                        form=form,
                        commande=commande,
                        num_com = num_commande)

@app.route("/client/fidelite")
@login_required
def client_fidelite():
    all_reductions = Reduction.query.order_by(Reduction.points_fidelite).all()
    all_plats = Plats.query.all()
    plats_map = {p.id_plat: p for p in all_plats}
    
    return render_template("fidelite_client.html",
                           reductions=all_reductions,
                           plats_map=plats_map)

from sqlalchemy.exc import OperationalError

@app.route("/echanger_points", methods=["POST"])
@login_required
def echanger_points():
    rid = request.form.get("id_reduction")
    reduction = Reduction.query.get(rid)
    if not reduction:
        flash("Réduction introuvable.", "danger")
        return redirect(url_for("client_fidelite"))

    if current_user.points_fidelite < reduction.points_fidelite:
        flash("Vous n'avez pas assez de points pour cette réduction.", "danger")
        return redirect(url_for("client_fidelite"))

    try:
        current_user.points_fidelite -= reduction.points_fidelite
        current_user.reductions.append(reduction)
        db.session.commit()
        flash(f"La réduction sur le plat {reduction.id_plat} a bien été achetée !", "success")

    except OperationalError as op_err:
        db.session.rollback()
        err_no, err_msg = op_err.orig.args  

        flash(f"Une erreur s'est produite lors de l'achat : {err_msg}", "danger")

    except Exception as e:
        db.session.rollback()
        flash(f"Une erreur s'est produite lors de l'achat : {e}", "danger")

    return redirect(url_for("client_fidelite"))

@app.route("/retourner_reduction", methods=["POST"])
@login_required
def retourner_reduction():
    rid = request.form.get("id_reduction")
    reduction = Reduction.query.get(rid)
    if not reduction:
        flash("Réduction introuvable.", "danger")
        return redirect(url_for("client_fidelite"))
    
    if reduction not in current_user.reductions:
        flash("Vous ne possédez pas cette réduction.", "danger")
        return redirect(url_for("client_fidelite"))
    
    try:
        current_user.points_fidelite += reduction.points_fidelite
        current_user.reductions.remove(reduction)
        db.session.commit()
        flash(f"La réduction sur le plat {reduction.id_plat} a été annulée, vos points ont été restaurés !", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Une erreur s'est produite lors de l'échange : {e}", "danger")
    
    return redirect(url_for("client_fidelite"))




