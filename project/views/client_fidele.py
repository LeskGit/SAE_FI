from project import app, db
from flask import render_template, url_for, redirect, request
from project.models import Commandes
from flask_wtf import FlaskForm
from flask_login import login_user , current_user, logout_user, login_required
from hashlib import sha256
from project.views.authentification import RegisterForm
from wtforms import StringField, PasswordField, EmailField
from wtforms.validators import DataRequired, EqualTo, Email, Length, Regexp

class PersoForm(FlaskForm):
    phone_number = StringField("Téléphone", validators=[DataRequired(), 
                                                               Length(min=10, max=10, message = 'Longueur incorrecte.'),
                                                               Regexp(r'^\d{10}$', message="Le numéro de téléphone est invalide.")])
    name = StringField("Nom", validators=[DataRequired(), 
                                          Length(max=32)])
    
    first_name = StringField("Prénom", validators=[DataRequired(), 
                                                   Length(max=32)])
    
    address = StringField("Adresse", validators=[DataRequired(), Length(max=64)])
    email = EmailField("Email", validators=[DataRequired(), Email(message='addresse mail invalide'), 
                                            Length(max=64)])

@app.route("/client/profil", methods=["GET", "POST"])
@login_required
def client_profil():
    f = PersoForm()
    
    edit = request.args.get('edit', False, type=bool)

    if f.validate_on_submit():        
        current_user.num_tel = f.phone_number.data
        current_user.nom = f.name.data
        current_user.prenom = f.first_name.data
        current_user.adresse = f.address.data
        current_user.email = f.email.data
        db.session.commit()
        return redirect(url_for("client_profil"))
    
    f = PersoForm(phone_number=current_user.num_tel,
                name=current_user.nom,
                first_name=current_user.prenom,
                address=current_user.adresse,
                email=current_user.email)

    return render_template("profil_client_connecte.html", form=f, edit=edit)

@app.route("/client/historique")
@login_required
def client_historique():
    # On récupère toutes les commandes de l'utilisateur
    commandes = Commandes.query.filter_by(num_tel=current_user.num_tel).order_by(Commandes.date_creation.desc()).all()
    
    historique = []
    for com in commandes:
        # On mappe l'état de la commande à un statut visuel
        if com.etat == "Payée":
            statut_label = "TERMINE"
            statut_class = "status-termine"
        else:
            statut_label = "EN COURS"
            statut_class = "status-encours"
        
        # Calcul du total de la commande et liste des plats
        if com.constituer_assoc:
            plats_names = ", ".join([assoc.plat.nom_plat for assoc in com.constituer_assoc])
            total_price = sum([assoc.plat.prix * assoc.quantite_plat for assoc in com.constituer_assoc])
        else:
            plats_names = "-"
            total_price = "-"
        
        # Une entrée par commande
        historique.append({
            "num_commande": str(com.num_commande).zfill(8),
            "plat": plats_names,
            "prix": total_price,
            "statut_label": statut_label,
            "statut_class": statut_class,
            "date_str": com.date.strftime('%Y/%m/%d') if com.date else '-',
            "heure_str": com.date.strftime('%H:%M') if com.date else '-'
        })

    return render_template("historique_commandes.html", historique=historique)

@app.route("/client/fidelite")
@login_required
def client_fidelite():
    return render_template("fidelite_client.html")

@app.route("/client/modif")
@login_required
def client_modif():
    return render_template("modif_commande.html")